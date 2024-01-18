

"""
Pydantic Schemas for the API
"""
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Optional, Dict, Union, Any
from uuid import UUID
from datetime import datetime
from llama_index.schema import BaseNode, NodeWithScore
from llama_index.callbacks.schema import EventPayload
from llama_index.query_engine.sub_question_query_engine import SubQuestionAnswerPair

from app.core.constants import DB_DOC_ID_KEY


def build_uuid_validator(*field_names: str):
    return validator(*field_names)(lambda x: str(x) if x else x)


class Base(BaseModel):
    id: Optional[UUID] = Field(None, description="Unique identifier")
    created_at: Optional[datetime] = Field(None, description="Creation datetime")
    updated_at: Optional[datetime] = Field(None, description="Update datetime")

    class Config:
        orm_mode = True
        from_attributes=True


class BaseMetadataObject(BaseModel):
    class Config:
        orm_mode = True
        from_attributes=True


class CitationSchema(BaseMetadataObject):
    document_id: UUID
    text: str
    page_number: int
    score: Optional[float]

    @validator("document_id")
    def validate_document_id(cls, value):
        if value:
            return str(value)
        return value

    @classmethod
    def from_node(cls, node_w_score: NodeWithScore) -> "Citation":
        node: BaseNode = node_w_score.node
        page_number = int(node.source_node.metadata["page_label"])
        document_id = node.source_node.metadata[DB_DOC_ID_KEY]
        return cls(
            document_id=document_id,
            text=node.get_content(),
            page_number=page_number,
            score=node_w_score.score,
        )



DocumentMetadataMap = Dict[str, Any]


class DocumentSchema(Base):
    url: str
    name: Optional[str]
    assistant_id: Optional[str]
    metadata_map: Optional[DocumentMetadataMap] = None