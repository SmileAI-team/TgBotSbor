from sqlalchemy.orm import Mapped

from .base import Base


class Users(Base):
    telegram_id: Mapped[str]
    card_number: Mapped[str]
