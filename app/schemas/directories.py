from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .files import File
import uuid


class DirectoryBase(BaseModel):
    name: str
    uid: uuid.UUID
    parent_uid: uuid.UUID | None
    access_level: int
    public_link: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DirectoryCreate(BaseModel):
    parent_uid: uuid.UUID | None


class DirectoryUpdate(DirectoryBase):
    pass

class Directory(DirectoryBase):
    children: list[DirectoryBase]
    files: list[File]

class DirectoryRoot(BaseModel):
    children: list[DirectoryBase]
    files: list[File]


