from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from llama_index.chat_engine.types import BaseChatEngine
from llama_index.core.base_query_engine import BaseQueryEngine
from llama_index.llms.base import ChatMessage
from llama_index.llms.types import MessageRole
from pydantic import BaseModel
from typing import Dict, Any

from app.engine.index import get_chat_engine, get_query_engine

router = r = APIRouter()


class _QueryData(BaseModel):
    query: str


class _Result(BaseModel):
    result: str
    forwardToClientEnabled: bool


@r.post("")
async def query(
    data: _QueryData,
    query_engine: BaseQueryEngine = Depends(get_query_engine),
) -> _Result:
    # check preconditions and get last message
    if not data.query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No query provided",
        )

    # query chat engine
    response = await query_engine.aquery(data.query)
    print(response.response)
    return _Result(
        result=response.response, 
        forwardToClientEnabled=True
    )


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

