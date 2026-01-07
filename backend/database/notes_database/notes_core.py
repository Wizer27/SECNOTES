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
            

async def delete_all_notes_that_need_to_be_deleted_now(time:str):
    async with AsyncSession(async_engine) as conn:
        try:
            now = datetime.now()
            formatted = now.strftime("%Y-%m-%d %H:%M")
            stmt = select(notes_table.id).where(notes_table.c.time_to_die == formatted)
            res = await conn.execute(stmt)
            data = res.fetchall()
            id_s_to_delete = []
            if data is not None:
                for dt in data:
                    id_s_to_delete.append(str(dt[0]))
                for note_id in id_s_to_delete:
                    await delete_note(note_id)        
        except exc.SQLAlchemyError as conn:
            raise exc.SQLAlchemyError("Error while executing")
        
async def get_note_text_by_id(note_id:str) -> str:
    if await is_notes_exists(note_id):
        async with AsyncSession(async_engine) as conn:
            try:
                stmt = select(notes_table.c.note).where(notes_table.c.id == note_id)
                res = await conn.execute(stmt)
                data = res.scalar_one_or_none()
                if data is not None:
                    return str(data)
                return ""
            except exc.SQLAlchemyError:
                raise exc.SQLAlchemyError("Error while executing")  
    raise NameError("Note not found")          

async def try_acces_note(note_id:str,try_psw:str):
    if not await is_notes_exists(note_id):
        return False
    async with AsyncSession(async_engine) as conn:
        try:
            stmt = select(notes_table.c.passwrord).where(notes_table.c.id == note_id)
            res = await conn.execute(stmt)
            data = res.scalar_one_or_none()
            if data is not None:
                if data == try_psw:
                    return await get_note_text_by_id(note_id)
            return False
        except exc.SQLAlchemyError:
            raise exc.SQLAlchemyError("Error while executing")