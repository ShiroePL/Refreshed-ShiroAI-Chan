from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime
from sqlalchemy import func

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

class ContextChoice(Base):
    __tablename__ = 'context_choices'
    
    id = Column(Integer, primary_key=True)
    context_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 

class AllDescriptions(Base):
    __tablename__ = 'all_descriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)