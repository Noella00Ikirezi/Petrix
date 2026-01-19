from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EventBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    category: str = Field(..., max_length=50)
    is_task: bool = False
    task_id: Optional[int] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=50)
    is_task: Optional[bool] = None
    task_id: Optional[int] = None


class EventResponse(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
