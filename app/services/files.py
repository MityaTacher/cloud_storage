import aiofiles
import os

from fastapi import UploadFile

from app.core.config import settings
from app.schemas.files import FileMetadata

import logging

async def save_file(file: UploadFile) -> FileMetadata:
    os.makedirs(settings.upload_dir, exist_ok=True)

    filepath = os.path.join(settings.upload_dir, file.filename)

    async with aiofiles.open(filepath, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)

    size_bytes = os.path.getsize(filepath)

    logging.error(f'Size: {size_bytes}; {file.size}')
    new_file = FileMetadata(
        filename=file.filename,
        filepath=filepath,
        size_bytes=size_bytes
    )
    return new_file

