from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pinecone import Pinecone
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB connections
    app.state.db_engine = create_async_engine(
        "mysql+aiomysql://user:pass@host/db",
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=10
    )
    app.state.async_session = sessionmaker(
        app.state.db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Initialize Pinecone
    app.state.pinecone = Pinecone(api_key="your-key")
    app.state.index = app.state.pinecone.Index("your-index")
    
    yield
    
    # Cleanup
    await app.state.db_engine.dispose()

app = FastAPI(lifespan=lifespan) 