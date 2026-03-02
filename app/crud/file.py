from fastapi import HTTPException, status, UploadFile
from fastapi.responses import FileResponse

from sqlalchemy import Sequence, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FileModel, UserModel
from app.services.files import save_file


async def get_files(
        session: AsyncSession
) -> Sequence[FileModel]:
    tmp = await session.scalars(select(FileModel))
    return tmp.all()


async def get_file(
        file_id: int,
        session: AsyncSession,
) -> FileModel:
    tmp = await session.scalars(
        select(FileModel)
        .where(FileModel.id == file_id)
    )
    file = tmp.first()
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found'
        )
    return file


async def create_file(
        user_id: int,
        file: UploadFile,
        session: AsyncSession
) -> FileModel:

    tmp = await session.scalars(
        select(UserModel)
        .where(UserModel.id == user_id)
    )
    if tmp.first() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User not found'
        )

    saved_file = await save_file(file)
    db_file = FileModel(
        user_id=user_id,
        filename=saved_file.filename,
        path=saved_file.filepath,
        size_bytes=saved_file.size_bytes
    )
    session.add(db_file)
    await session.commit()
    await session.refresh(db_file)
    return db_file


async def delete_file(
        file_id: int,
        session: AsyncSession
) -> None:
    tmp = await session.scalars(
        select(FileModel)
        .where(FileModel.id == file_id)
    )
    db_file = tmp.first()
    if db_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found'
        )

    #TODO реальное удаление файла

    await session.delete(db_file)
    await session.commit()
    return


async def download_file(file_id: int, session: AsyncSession) -> FileResponse:
    tmp = await session.scalars(
        select(FileModel)
        .where(FileModel.id == file_id)
    )
    db_file = tmp.first()
    if db_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found'
        )

    return FileResponse(
        path=db_file.path,
        filename=db_file.filename,
        media_type='application/octet-stream'
    )

