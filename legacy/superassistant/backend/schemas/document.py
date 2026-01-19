from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentBase(BaseModel):
    title: str = Field(..., max_length=200)
    type: str = Field(..., max_length=50)
    content: str
    status: str = Field(default="draft", max_length=20)
    version: str = Field(default="1.0", max_length=20)
    tags: Optional[List[str]] = []


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    type: Optional[str] = Field(None, max_length=50)
    content: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    version: Optional[str] = Field(None, max_length=20)
    tags: Optional[List[str]] = None


class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
