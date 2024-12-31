from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = 'private_conversations'  # Changed from 'chatgpt_api'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text)  # Original 'Question' column
    answer = Column(Text)    # Original 'Answer' column
    added_time = Column(DateTime, default=datetime.utcnow)

class ApiUsage(Base):
    __tablename__ = 'chatgpt_api_usage'  # Using the existing table name
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    added_time = Column(DateTime, default=datetime.utcnow) 