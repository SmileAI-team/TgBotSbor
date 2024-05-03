from fastapi import APIRouter

router = APIRouter(prefix="/users")

@router.get("/")
def get_users():
    return [
        "item1",
        "item2"
    ]

@router.get("/{user_id}/")
def get_user_by_id(user_id):
    return {
        "item": {
            "id": user_id,
        },
    }

@router.post("/create_user")
def create_user(user_id):
    return {
        'users':{
            "new_user": user_id
        }
    }