from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import Column, Integer, String
from typing import List

from .base import Base


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    card_number = Column(String, unique=True)
    google_path: Mapped[str] = mapped_column(String, nullable=True)


    items: Mapped[List["Items"]] = relationship("Items", back_populates="user")
