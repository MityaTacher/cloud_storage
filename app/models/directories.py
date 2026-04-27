from datetime import datetime

from app.db.base import Base

from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy import Integer, String, ForeignKey, UUID, DateTime, func

import uuid

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.files import File
    from app.models.users import User



class Directory(Base):
    __tablename__ = 'directories'

    uid: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=lambda: uuid.uuid4())
    name: Mapped[str] = mapped_column(String, unique=False, nullable=False, default='dir', server_default='dir')

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    user: Mapped['User'] = relationship(
        'User',
        back_populates='directories'
    )

    parent_uid: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('directories.uid', ondelete='CASCADE'),
        nullable=True
    )
    parent: Mapped["Directory | None"] = relationship(
        "Directory",
        back_populates='children',
        remote_side='Directory.uid'
    )

    children: Mapped[list['Directory']] = relationship(
        'Directory',
        back_populates='parent',
        cascade='all, delete-orphan'
    )
    files: Mapped[list['File']] = relationship(
        'File',
        back_populates='parent',
        cascade='all, delete-orphan'
    )
    public_link: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4(), nullable=False)
    access_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


