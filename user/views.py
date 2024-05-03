from fastapi import APIRouter

from user.schemas import CreateUser
from user import crud

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/")
def create_user(user: CreateUser):
    return crud.create_user(user_in=user)