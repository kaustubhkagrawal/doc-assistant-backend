from llama_index import ServiceContext
from llama_index.embeddings.openai import (
    OpenAIEmbedding,
    OpenAIEmbeddingMode,
    OpenAIEmbeddingModelType
)
from llama_index.llms import OpenAI
from llama_index.node_parser import SentenceSplitter

from app.context import create_base_context
from app.core.config import settings
from app.engine.constants import CHUNK_SIZE, CHUNK_OVERLAP, NODE_PARSER_CHUNK_OVERLAP, NODE_PARSER_CHUNK_SIZE



OPENAI_TOOL_LLM_NAME = "gpt-3.5-turbo-0613"
OPENAI_CHAT_LLM_NAME = "gpt-3.5-turbo-0613"


def create_service_context():
    base = create_base_context()
    return ServiceContext.from_defaults(
        llm=base.llm,
        embed_model=base.embed_model,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

def create_tool_service_context() -> ServiceContext:
    llm = OpenAI(
        temperature=0,
        model=OPENAI_TOOL_LLM_NAME,
        streaming=False,
        api_key=settings.OPENAI_API_KEY,
    )
    embedding_model = OpenAIEmbedding(
        mode=OpenAIEmbeddingMode.SIMILARITY_MODE,
        model_type=OpenAIEmbeddingModelType.TEXT_EMBED_ADA_002,
        api_key=settings.OPENAI_API_KEY,
    )
    # Use a smaller chunk size to retrieve more granular results
    node_parser = SentenceSplitter.from_defaults(
        chunk_size=NODE_PARSER_CHUNK_SIZE,
        chunk_overlap=NODE_PARSER_CHUNK_OVERLAP,
    )
    service_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=embedding_model,
        node_parser=node_parser,
    )
    return service_context