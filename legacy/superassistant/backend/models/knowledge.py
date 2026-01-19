from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from database import Base


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # template/solution/note/reference
    tags = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
