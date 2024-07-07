
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Items
from .schemas import ItemCreate, ItemUpdate


async def get_items(session: AsyncSession) -> list:
    stmt = select(Items).order_by(Items.id)
    result = await session.execute(stmt)
    items = result.scalars().all() if result else []
    return items

async def get_item(session: AsyncSession, item_id: int):
    return await session.get(Items, item_id)

async def create_item(session: AsyncSession, item_in: ItemCreate):
    item = Items(**item_in.dict())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

async def update_item(session: AsyncSession, item_id: int, item_in: ItemUpdate):
    stmt = (
        update(Items)
        .where(Items.id == item_id)
        .values(**item_in.dict())
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0

async def delete_item(session: AsyncSession, item_id: int):
    stmt = delete(Items).where(Items.id == item_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0

