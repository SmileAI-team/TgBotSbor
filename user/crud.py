"""
Create
Read
Update
Delete
"""

from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.models import Users

from .schemas import UserCreate


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
