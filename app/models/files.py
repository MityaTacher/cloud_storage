from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, func, ForeignKey, UUID, BigInteger

from datetime import datetime
import uuid

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.users import User
    from app.models.directories import Directory
    from app.models.nodes import StorageNode

class File(Base):
    __tablename__ = 'files'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user: Mapped['User'] = relationship('User', back_populates='files')
    access_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    uid: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False, index=True, default=lambda: uuid.uuid4())

    parent_uid: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('directories.uid', ondelete='CASCADE'), nullable=True)
    parent: Mapped['Directory | None'] = relationship('Directory', back_populates='files')

    status: Mapped[str] = mapped_column(String, default="PENDING", nullable=False)
    node_id: Mapped[int | None] = mapped_column(ForeignKey('storage_nodes.id', ondelete='CASCADE'), nullable=True)
    node: Mapped['StorageNode | None'] = relationship('StorageNode', back_populates='files')
