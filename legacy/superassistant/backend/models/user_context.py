from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base


class UserContext(Base):
    __tablename__ = "user_context"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # profile/preferences/schedule/history
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
