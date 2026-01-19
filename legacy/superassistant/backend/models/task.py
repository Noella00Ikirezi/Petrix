from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # Études/SMSI/Support/Projets/Personnel
    priority = Column(String(20), nullable=False, default="moyenne")  # haute/moyenne/basse
    status = Column(String(20), nullable=False, default="todo")  # todo/in_progress/completed/blocked
    deadline = Column(DateTime, nullable=True)
    estimated_time = Column(Float, nullable=True)  # En heures
    actual_time = Column(Float, nullable=True)
    tags = Column(JSON, nullable=True, default=list)  # Liste de tags
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="tasks")
