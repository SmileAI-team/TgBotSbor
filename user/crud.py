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
