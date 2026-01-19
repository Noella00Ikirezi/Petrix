from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active")  # active/completed/archived
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    progress = Column(Float, default=0.0)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
