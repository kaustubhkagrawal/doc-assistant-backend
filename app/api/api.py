from fastapi import APIRouter

from app.api.routers import query, documents, assistant

api_router = APIRouter()

api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant", ])
