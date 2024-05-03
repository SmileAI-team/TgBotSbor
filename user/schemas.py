from pydantic import BaseModel


class CreateUser(BaseModel):
    id: id
    name: name
