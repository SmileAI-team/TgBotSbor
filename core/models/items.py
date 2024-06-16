from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from .base import Base
from .user import Users


class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    time = Column(DateTime, nullable=False)
    google_drive_path = Column(String, nullable=False)
    viewed = Column(Boolean, default=False)
    validated = Column(Boolean, default=False)
    comment = Column(String, nullable=True)

    user = relationship("Users", back_populates="items")
