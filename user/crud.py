"""
Create
Read
Update
Delete
"""

from sqlalchemy import select, update, delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from google_drive import create_folder

from core.config import settings
from core.models import Users

from .schemas import UserCreate, UserUpdate


async def get_users(session: AsyncSession) -> list:
    stmt = select(Users).order_by(Users.id)
    result: Result = await session.execute(stmt)
    users = result.scalars().all() if result else []
    return users

async def get_user(session: AsyncSession, user_id: int):
    return await session.get(Users, user_id)


async def create_user(session: AsyncSession, user_in: UserCreate):
    user = Users(**user_in.model_dump())
    session.add(user)
    await session.commit()
    # await session.refresh(user1)
    return user

async def update_user(session: AsyncSession, user_id: int, user_in: UserUpdate):
    stmt = (
        update(Users)
        .where(Users.id == user_id)
        .values(**user_in.dict())
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0

async def delete_user(session: AsyncSession, user_id: int):
    stmt = delete(Users).where(Users.id == user_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: str):
    stmt = select(Users).filter_by(telegram_id=telegram_id)
    result = await session.execute(stmt)
    return result.scalars().first()

async def create_user_with_telegram_id(session: AsyncSession, telegram_id: str):
    google_path = await create_folder(f"User_{telegram_id}", settings.google_drive_parent_folder_id)

    user_in = UserCreate(telegram_id=telegram_id, card_number="", google_path=google_path)
    user = Users(**user_in.dict())

    session.add(user)
    await session.commit()
    return user
