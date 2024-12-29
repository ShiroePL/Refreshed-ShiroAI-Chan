from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class UserMessage(Base):
    __tablename__ = 'user_messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    role = Column(String(50))
    content = Column(Text)
    added_time = Column(DateTime, default=datetime.utcnow)
    # Add any other fields from your existing table 