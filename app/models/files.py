from app.db.base import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, func, ForeignKey, UUID

from datetime import datetime
import uuid

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.users import User
    from app.models.directories import Directory


class File(Base):
    __tablename__ = 'files'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user: Mapped['User'] = relationship('User', back_populates='files')
    access_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    uid: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False, index=True, default=lambda: uuid.uuid4())

    parent_uid: Mapped[uuid.UUID] = mapped_column(ForeignKey('directories.uid', ondelete='CASCADE'), nullable=True)
    parent: Mapped['Directory'] = relationship('Directory', back_populates='files')

