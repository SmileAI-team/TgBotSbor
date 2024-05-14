from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    telegram_id: str
    card_number: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
