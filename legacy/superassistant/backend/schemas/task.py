from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    priority: str = Field(default="moyenne", max_length=20)
    status: str = Field(default="todo", max_length=20)
    deadline: Optional[datetime] = None
    estimated_time: Optional[float] = None
    actual_time: Optional[float] = None
    tags: Optional[List[str]] = []
    project_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    deadline: Optional[datetime] = None
    estimated_time: Optional[float] = None
    actual_time: Optional[float] = None
    tags: Optional[List[str]] = None
    project_id: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
