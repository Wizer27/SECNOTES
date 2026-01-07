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
import uuid


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

async def is_notes_exists(note_id:str) -> bool:
    async with AsyncSession(async_engine) as conn:
        try:
            stmt = select(notes_table.id).where(notes_table.id == note_id)
            res = await conn.execute(stmt)
            result = res.scalar_one_or_none()
            return result is not None
        except exc.SQLAlchemyError:
            raise exc.SQLAlchemyError("Error while executing")

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
                    time_to_die = time_to_die,
                    id = str(uuid.uuid4())
                )
                await conn.execute(stmt)
            except exc.SQLAlchemyError:
                raise exc.SQLAlchemyError("Error while executing")

async def get_all_user_notes(username:str) -> dict:
    async with AsyncSession(async_engine) as conn:
        try:
            stmt = select(notes_table.c.note).where(notes_table.c.username == username)
            res = await conn.execute(stmt)
            data = res.fetchall()
            if data is not None:
                notes = []
                for sm in data:
                    notes.append(sm[0])
                new_stmt = select(notes_table.c.id).where(notes_table.c.username == username)
                res2 = await conn.execute(new_stmt)
                data2 = res2.fetchall()
                id_s = []
                for dt in data2:
                    id_s.append(dt[0])
                result = {}    
                if notes != [] and id_s != []:
                    for note_id in id_s:
                        for note in notes:
                            result[note_id] = note
                return result            
            return {}
        except exc.SQLAlchemyError:
            raise exc.SQLAlchemyError("Error while executing") 

async def delete_note(note_id:str) -> bool:
    if not await is_notes_exists(note_id):
        return False
    async with AsyncSession(async_engine) as conn:
        async with conn.begin():
            try:
                stmt = notes_table.delete(notes_table).where(notes_table.c.id == note_id)
                await conn.execute(stmt)
            except exc.SQLAlchemyError:
                raise exc.SQLAlchemyError("Error while executing")

