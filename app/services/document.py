from typing import Optional, Sequence, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from uuid import UUID

from app.db.session import SessionLocal
from app.models.db import Document
from app.schemas.base import DocumentSchema
from app.utils.file_utils import generate_name_from_url




async def fetch_documents(
    db: AsyncSession,
    id: Optional[str] = None,
    ids: Optional[List[str]] = None,
    assistant_id: Optional[str] = None,
    url: Optional[str] = None,
    limit: Optional[int] = None,
) -> Optional[Sequence[DocumentSchema]]:
    """
    Fetch a document by its url or id
    """

    stmt = select(Document)
    if id is not None:
        stmt = stmt.where(Document.id == id)
        limit = 1
    elif assistant_id is not None:
        print(assistant_id)
        stmt = stmt.where(Document.assistant_id == assistant_id)
    elif ids is not None:
        stmt = stmt.where(Document.id.in_(ids))
    
    if url is not None:
        stmt = stmt.where(Document.url == url)
    if limit is not None:
        stmt = stmt.limit(limit)
        
    result = await db.execute(stmt)
    documents = result.scalars().all()
    return [DocumentSchema.from_orm(doc) for doc in documents]



async def upsert_single_document(doc_url: str):
    """
    Upserts a single SEC document into the database using its URL.
    """
    
    print("upsert_single_document called")
    if not doc_url or not doc_url.startswith('http'):
        print("DOC_URL must be an http(s) based url value")
        return
    metadata_map = {}
    name=generate_name_from_url(doc_url)
    doc = DocumentSchema(url=doc_url, name=name, assistant_id="", metadata_map=metadata_map)


    async with SessionLocal() as db:
        document = await upsert_document_by_url(db, doc)

    return document




async def upsert_document_by_url(
    db: AsyncSession, document: DocumentSchema
) -> DocumentSchema:
    """
    Upsert a document
    """
    print(document.model_dump())
    stmt = insert(Document).values(**document.model_dump(exclude_none=True))
    stmt = stmt.on_conflict_do_update(
        index_elements=[Document.url],
        set_=document.model_dump(include={"metadata_map"}),
    )
    stmt = stmt.returning(Document)
    result = await db.execute(stmt)
    upserted_doc = DocumentSchema.from_orm(result.scalars().first())
    await db.commit()
    return upserted_doc


async def update_assistant_to_document(
     db: AsyncSession, 
    document_id: UUID, 
    assistant_id: str  
):
    """
    update assistant_id into the document
    """
    
    stmt = update(Document).where(Document.id==document_id).values(assistant_id=assistant_id)
    
    stmt = stmt.returning(Document)
    result = await db.execute(stmt)
    updated_doc = DocumentSchema.from_orm(result.scalars().first())
    await db.commit()
    return updated_doc