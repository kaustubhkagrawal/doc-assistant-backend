from typing import Optional, cast, Sequence, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import Document
from app.db.session import SessionLocal
from app.schemas import base
from sqlalchemy.dialects.postgresql import insert


async def upsert_single_document(doc_url: str):
    """
    Upserts a single SEC document into the database using its URL.
    """
    
    print("upsert_single_document called")
    if not doc_url or not doc_url.startswith('http'):
        print("DOC_URL must be an http(s) based url value")
        return
    metadata_map = {}
    doc = base.Document(url=doc_url, metadata_map=metadata_map)


    async with SessionLocal() as db:
        document = await upsert_document_by_url(db, doc)

    return document




async def upsert_document_by_url(
    db: AsyncSession, document: base.Document
) -> base.Document:
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
    upserted_doc = base.Document.from_orm(result.scalars().first())
    await db.commit()
    return upserted_doc