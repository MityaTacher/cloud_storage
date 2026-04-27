from pydantic import Field, BaseModel, ByteSize, ConfigDict
from datetime import datetime

import uuid


class FileMetadata(BaseModel):
    """
    Модель для получения данных о файле после сохранения
    """
    filename: str
    filepath: str
    size_bytes: int
    parent_uid: uuid.UUID | None
    access: int


class FileBase(BaseModel):
    """

    """
    user_id: int = Field(description='id пользователя, загрузившего файл')


class FileCreate(BaseModel):
    """

    """
    pass


class File(FileBase):
    """

    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='id файла в базе данных')
    filename: str = Field(max_length=50, description='Имя файла')
    # path: FilePath = Field(description='Путь, где сохранен файл')
    size_bytes: ByteSize = Field(description='Размер файла')
    loaded_at: datetime = Field(description='Время загрузки файла')
    access_level: int = Field(ge=0, le=1, description='Права доступа')
    uid: uuid.UUID = Field(default=lambda: uuid.uuid4(), description='Публичная ссылка на файл')
    parent_uid: uuid.UUID | None = Field(description='В какой папке находится')
