import aiofiles
import os
import uuid

from fastapi import UploadFile

from app.core.config import settings
from app.schemas.files import FileMetadata

import logging

async def save_file(file: UploadFile, parent_uid: uuid.UUID | None) -> FileMetadata:
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Prefix with UUID to prevent filename collisions between users
    safe_name = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(settings.upload_dir, safe_name)

    async with aiofiles.open(filepath, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)

    size_bytes = os.path.getsize(filepath)

    new_file = FileMetadata(
        filename=file.filename,   # keep original name for display
        filepath=filepath,
        size_bytes=size_bytes,
        parent_uid=parent_uid,
        access=0
    )
    return new_file


