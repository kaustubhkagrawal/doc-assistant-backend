from typing import Dict, List, Optional
import logging

from pathlib import Path
from tempfile import TemporaryDirectory
import requests
from fsspec.asyn import AsyncFileSystem


from cachetools import cached, TTLCache
from datetime import timedelta

from llama_index import (
    ServiceContext,
    VectorStoreIndex,
    StorageContext,
    load_indices_from_storage,
)
from llama_index.indices.query.base import BaseQueryEngine
from llama_index.readers.file.docs_reader import PDFReader
from llama_index.schema import Document as LlamaIndexDocument
from llama_index.vector_stores.types import (
    VectorStore,
    MetadataFilters,
    ExactMatchFilter,
)



from app.schemas.base import DocumentSchema
from app.core.constants import (
    DB_DOC_ID_KEY
)
from app.core.config import settings
from app.db.pg_vector import get_vector_store_singleton



logger = logging.getLogger(__name__)


@cached(
    TTLCache(maxsize=10, ttl=timedelta(minutes=5).total_seconds()),
    key=lambda *args, **kwargs: "global_storage_context",
)
def get_storage_context(
    persist_dir: str, vector_store: VectorStore, fs: Optional[AsyncFileSystem] = None
) -> StorageContext:
    logger.info("Creating new storage context.")
    return StorageContext.from_defaults(
        persist_dir=persist_dir, vector_store=vector_store, fs=fs
    )



def build_description_for_document(document: DocumentSchema) -> str:
    return f"A document with id {document.id} containing some useful information."





def index_to_query_engine(doc_id: str, index: VectorStoreIndex) -> BaseQueryEngine:
    filters = MetadataFilters(
        filters=[ExactMatchFilter(key=DB_DOC_ID_KEY, value=doc_id)]
    )
    kwargs = {"similarity_top_k": 3, "filters": filters}
    return index.as_query_engine(**kwargs)


def fetch_and_read_document(
    document: DocumentSchema,
) -> List[LlamaIndexDocument]:
    # Super hacky approach to get this to feature complete on time.
    # TODO: Come up with better abstractions for this and the other methods in this module.
    with TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / f"{str(document.id)}.pdf"
        with open(temp_file_path, "wb") as temp_file:
            with requests.get(document.url, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
            temp_file.seek(0)
            reader = PDFReader()
            return reader.load_data(
                temp_file_path, extra_info={DB_DOC_ID_KEY: str(document.id)}
            )


async def create_index_from_doc(
    service_context: ServiceContext,
    document: DocumentSchema,
    fs: Optional[AsyncFileSystem] = None,
):
    
    persist_dir = f"{settings.S3_BUCKET_NAME}"

    vector_store = await get_vector_store_singleton()
    try:
        try:
            storage_context = get_storage_context(persist_dir, vector_store, fs=fs)
        except FileNotFoundError:
            logger.info(
                "Could not find storage context in S3. Creating new storage context."
            )
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store, fs=fs
            )
            storage_context.persist(persist_dir=persist_dir, fs=fs)
        index_ids = [str(document.id)]
        indices = load_indices_from_storage(
            storage_context,
            index_ids=index_ids,
            service_context=service_context,
        )
        doc_id_to_index = dict(zip(index_ids, indices))
        logger.debug("Loaded indices from storage.")
    except ValueError:
        logger.error(
            "Failed to load indices from storage. Creating new indices. "
            "If you're running the seed_db script, this is normal and expected."
        )
        storage_context = StorageContext.from_defaults(
            persist_dir=persist_dir, vector_store=vector_store, fs=fs
        )
        doc_id_to_index = {}

        llama_index_docs = fetch_and_read_document(document)
        storage_context.docstore.add_documents(llama_index_docs)
        index = VectorStoreIndex.from_documents(
            llama_index_docs,
            storage_context=storage_context,
            service_context=service_context,
        )
        index.set_index_id(str(document.id))
        index.storage_context.persist(persist_dir=persist_dir, fs=fs)
        doc_id_to_index[str(document.id)] = index
    return doc_id_to_index