from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # politique/procedure/guide/registre/rapport/cr
    content = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft/review/approved/archived
    version = Column(String(20), default="1.0")
    tags = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
