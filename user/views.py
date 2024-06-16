from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.models import db_helper
from .schemas import User, UserCreate, UserUpdate
from . import crud

router = APIRouter(tags=["Users"], prefix="/users")


@router.get("/list", response_model=List[User])
async def get_users(
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.get_users(session=session)


@router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.create_user(session=session, user_in=user_in)


@router.get("/{user_id}/", response_model=User)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    user = await crud.get_user(session=session, user_id=user_id)
    if user is not None:
        return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User {user_id} not found",
    )

@router.put("/{user_id}/", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    updated = await crud.update_user(session=session, user_id=user_id, user_in=user_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return await crud.get_user(session=session, user_id=user_id)

@router.delete("/{user_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    deleted = await crud.delete_user(session=session, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return {"message": "User deleted successfully"}
