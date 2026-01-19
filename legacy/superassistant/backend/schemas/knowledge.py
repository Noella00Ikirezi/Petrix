from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class KnowledgeBase(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    category: str = Field(..., max_length=50)
    tags: Optional[List[str]] = []


class KnowledgeCreate(KnowledgeBase):
    pass


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None


class KnowledgeResponse(KnowledgeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
