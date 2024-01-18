from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from llama_index.core.base_query_engine import BaseQueryEngine
from llama_index.query_engine import CitationQueryEngine
from llama_index.vector_stores.types import (
    MetadataFilters,
    ExactMatchFilter,
)

from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.constants import DB_DOC_ID_KEY
from app.engine.context import create_tool_service_context
from app.engine.index import get_query_engine
from app.engine.indexing import create_index_from_doc
from app.schemas.base import CitationSchema
from app.services.document import fetch_documents
from app.utils.file_utils import  get_s3_fs


router = r = APIRouter()


class _QueryData(BaseModel):
    query: str
    doc_id: str


class _Result(BaseModel):
    result: str
    sources: Optional[List[CitationSchema]]
    forwardToClientEnabled: bool



@r.post("")
async def query_document(
    data: _QueryData,
    query_engine: BaseQueryEngine = Depends(get_query_engine),
    db: AsyncSession = Depends(get_db),
) -> _Result:
    # check preconditions and get last message
    if not data.query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No query provided",
        )
        
    if not data.doc_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No doc id provided",
        )

    service_context = create_tool_service_context()
    fs = get_s3_fs()

    try:
        doc_id = data.doc_id
        documents = await fetch_documents(db=db, id=doc_id)
        document = documents[0]
        indexDict = await create_index_from_doc(service_context=service_context, document=document, fs=fs)
        print(indexDict)
        index = indexDict[str(document.id)]

        filters = MetadataFilters(
            filters=[ExactMatchFilter(key=DB_DOC_ID_KEY, value=doc_id)]
        )
        # query_engine = index.as_query_engine(filters=filters, similarity_top_k=3)
        query_engine = CitationQueryEngine.from_args(index=index,filters=filters, similarity_top_k=3)
        
        response = await query_engine.aquery(data.query)
        print(response.response)
        
        citations = [
            CitationSchema.from_node(node_w_score=node)
            for node in response.source_nodes
        ]
        
        return _Result(
            result=response.response, 
            sources=citations,
            forwardToClientEnabled=True
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to index the Document")

# @r.post("/assistant")
# async def assistant(
#     data: Dict[Any, Any],
#     query_engine: BaseQueryEngine = Depends(get_query_engine),
# ) -> _Result:
    
#     if not data.message or data.message.type != 'function-call':
#         return _Result()
    
#     function_call = data.message.functionCall
#     fn_name = function_call.name
#     parameters = function_call.parameters
#     if fn_name == 'queryBook':
#         response = await query_engine.aquery(parameters.query)    
#         return _Result(
#             response=response.response
#         )
            

#     return _Result()

