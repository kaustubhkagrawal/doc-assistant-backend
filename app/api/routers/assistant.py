import httpx
from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID


from app.api.deps import get_db
from app.core.config import settings
from app.assistant.doc_reader import assistant_data

from app.db.session import SessionLocal
from app.services.document import update_assistant_to_document, fetch_documents


from sqlalchemy.ext.asyncio import AsyncSession

router = r = APIRouter()

@router.get("/{document_id}")
async def assistant_handler(
    document_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    try:
        print("Start")
        documents = await fetch_documents(db=db, id=document_id)
        document = documents[0]
        
        if True:
            headers = {"Authorization": f"Bearer {settings.VAPI_API_SECRET}"}
            
            async with httpx.AsyncClient() as client:
                # Make a POST request to the third-party API
                response = await client.post(
                    f"{settings.VAPI_BASE_URL}/assistant",
                    json={**assistant_data, "name": f"document-reader-{document_id}"},
                    headers=headers,
                )
            print("response", response)

            if response.status_code == 201:
                assistant_id = response.json().get("id")
                document = await update_assistant_to_document(db, document_id=document_id,assistant_id=assistant_id)
                return document
            raise HTTPException(status_code=response.status_code, detail=response.json())
        # return document
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
