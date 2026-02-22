import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

#асинхронная сессия
async_create_engine = create_async_engine(os.getenv('ASYNC_LOCAL_DATABASE_URL'), echo = True)
async_session_maker = async_sessionmaker(async_create_engine, expire_on_commit=False, class_=AsyncSession)

# Синхронная сессия для Celery
sync_engine = create_engine(os.getenv("SYNC_LOCAL_DATABASE_URL"), echo=True)
SyncSessionLocal = sessionmaker(
    sync_engine, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass