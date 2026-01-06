from notes_models import metadata_obj,notes_table
from sqlalchemy import select,delete,and_,exc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime,timedelta
from typing import List,Optional
from sqlalchemy.orm import sessionmaker
import asyncpg
import os
from dotenv import load_dotenv
import asyncio
import atexit


load_dotenv()

async_engine = create_async_engine(
    f"postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@localhost:5432/secnotes_notes",
    pool_size=20,           # Размер пула соединений
    max_overflow=50,        # Максимальное количество соединений
    pool_recycle=3600,      # Пересоздавать соединения каждый час
    pool_pre_ping=True,     # Проверять соединение перед использованием
    echo=False
)


AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

async def create_table():
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata_obj.create_all)

async def get_all_data() -> Optional[List]:
    async with AsyncSession(async_engine) as conn:
        try:
            stmt = select(notes_table)
            res = await conn.execute(stmt)
            data = res.fetchall()
            return data
        except exc.SQLAlchemyError:
            raise exc.SQLAlchemyError("Error")

async def write_note(username:str,note:str,note_psw:str,time_to_die:str):
    async with AsyncSession(async_engine) as conn:
        async with conn.begin():
            try:
                stmt = notes_table.insert().values(
                    username = username,
                    note = note,
                    password = note_psw,
                    time_to_die = time_to_die
                )
                await conn.execute(stmt)
            except exc.SQLAlchemyError:
                raise exc.SQLAlchemyError("Error while executing")

async def get_all_user_notes(username:str) -> Optional[List[str]]:
    async with AsyncSession(async_engine) as conn:
        try:
            stmt = select(notes_table.c.note).where(notes_table.c.username == username)
            res = await conn.execute(stmt)
            data = res.fetchall()
            if data is not None:
                result = []
                for sm in data:
                    result.append(sm[0])
                return result    
            return []
        except exc.SQLAlchemyError:
            raise exc.SQLAlchemyError("Error while executing")                
