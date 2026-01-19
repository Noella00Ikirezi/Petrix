from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    status: str = Field(default="active", max_length=20)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress: float = Field(default=0.0, ge=0, le=100)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress: Optional[float] = Field(None, ge=0, le=100)


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
