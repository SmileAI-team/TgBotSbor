

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.models import db_helper
from .schemas import Item, ItemCreate, ItemUpdate
from . import crud
from services import process_files

router = APIRouter(tags=["Items"], prefix="/items")


@router.get("/list", response_model=List[Item])
async def get_items(
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.get_items(session=session)


@router.post(
    "/",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
    item_in: ItemCreate,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.create_item(session=session, item_in=item_in)


@router.get("/{item_id}/", response_model=Item)
async def get_item(
    item_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    item = await crud.get_item(session=session, item_id=item_id)
    if item is not None:
        return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Item {item_id} not found",
    )

@router.put("/{item_id}/", response_model=Item)
async def update_item(
    item_id: int,
    item_in: ItemUpdate,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    updated = await crud.update_item(session=session, item_id=item_id, item_in=item_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return await crud.get_item(session=session, item_id=item_id)

@router.delete("/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    deleted = await crud.delete_item(session=session, item_id=item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return {"message": "Item deleted successfully"}

@router.post("/upload/")
async def upload_files(
    telegram_id: str = Form(...),
    files: List[UploadFile] = File(...),  # Используем List из typing
    comment: str = Form(...),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    file_contents = [await file.read() for file in files]
    response = await process_files(telegram_id, file_contents, comment, session)
    return response