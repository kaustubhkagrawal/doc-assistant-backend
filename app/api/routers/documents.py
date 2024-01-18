
from fastapi import APIRouter, UploadFile, HTTPException, File

from io import BytesIO
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
import s3fs


from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import CitationQueryEngine, BaseQueryEngine
from llama_index.vector_stores.types import (
    VectorStore,
    MetadataFilters,
    ExactMatchFilter,
)

from app.core.config import settings
from app.core.constants import DB_DOC_ID_KEY
from app.engine.indexing import create_index_from_doc, index_to_query_engine, build_description_for_document
from app.engine.context import create_tool_service_context
from app.schemas.base import DocumentSchema
from app.services.document import upsert_single_document
from app.utils.file_utils import get_Document_url, get_s3_fs


router = APIRouter()

# # Initialize S3 client
# s3_client = get_s3_client()

class FileData(BaseModel):
    file: UploadFile

ALLOWED_EXTENSIONS = ["pdf", "txt", "md", "jpg", "jpeg", "png", "gif"]

def is_allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# @router.post("/upload")
# async def upload_file_to_s3(file: UploadFile = File()):
#     print(file.filename)
#     if not is_allowed_file(file.filename):
#         raise HTTPException(status_code=400, detail="File type not allowed")

#     with BytesIO() as file_stream:
#         # Read the file into memory
#         file_stream.write(await file.read())
#         file_stream.seek(0)

#         # Upload the file to S3
#         try:
#             s3_client.upload_fileobj(file_stream, settings.S3_ASSET_BUCKET_NAME, file.filename)
#         except Exception as e:
#             print(e)
#             raise HTTPException(status_code=500, detail="Failed to upload Document")
        
#     url: str = get_Document_url(file_name=file.filename)
#     doc = await upsert_single_document(url)
#     doc_dict = jsonable_encoder(doc)
#     return doc_dict


@router.post("/upload")
async def upload_file_to_s3(file: UploadFile = File()):
    print(file.filename)
    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed")
    s3 = get_s3_fs(settings.S3_ASSET_BUCKET_NAME)

    with BytesIO() as file_stream:
        # Read the file into memory
        file_stream.write(await file.read())
        file_stream.seek(0)

        # Upload the file to S3 using s3fs
        with s3.open(f"{settings.S3_ASSET_BUCKET_NAME}/{file.filename}", "wb") as s3_file:
            s3_file.write(file_stream.read())

    url: str = get_Document_url(file_name=file.filename)
    doc = await upsert_single_document(url)
    doc_dict = jsonable_encoder(doc)
    return doc_dict


@router.post("/index")
async def upload_file_to_s3(document: DocumentSchema):
    
    print(document)
    
    service_context = create_tool_service_context()
    fs = get_s3_fs()

    try:
        doc_id = str(document.id)
        indexDict = await create_index_from_doc(service_context=service_context, document=document, fs=fs)
        print(indexDict)
        index = indexDict[str(document.id)]

        filters = MetadataFilters(
            filters=[ExactMatchFilter(key=DB_DOC_ID_KEY, value=doc_id)]
        )
        query_engine = index.as_query_engine(filters=filters, similarity_top_k=3)

        
        response = query_engine.query(f"Summarize the document {doc_id} within 500 words")
        return {
            "message": "Indexing Completed", 
            "result": response.response
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to index the Document")
        
    
    # return {"message": "INdexing completed"}
