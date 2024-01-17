from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base


class Document(Base):
    """
    A document along with its metadata
    """

    # URL to the actual document (e.g. a PDF)
    url = Column(String, nullable=False, unique=True)
    metadata_map = Column(JSONB, nullable=True)
