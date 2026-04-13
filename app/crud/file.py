import os

from fastapi import HTTPException, status, UploadFile
from fastapi.responses import FileResponse

from sqlalchemy import Sequence, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FileModel, UserModel
from app.services.files import save_file


async def check_file_permission(
        file_id: int,
        session: AsyncSession,
        user: UserModel,
        allow_admin: bool = False
) -> FileModel:
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
    if db_file.user_id != user.id and not (allow_admin and user.role == 'admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You cannot perform this action'
        )
    return db_file


async def get_files(
        session: AsyncSession
) -> Sequence[FileModel]:
    tmp = await session.scalars(select(FileModel))
    return tmp.all()


async def get_file(
        file_id: int,
        session: AsyncSession,
        user: UserModel
) -> FileModel:
    db_file = await check_file_permission(file_id, session, user, allow_admin=True)
    return db_file


async def create_file(
        file: UploadFile,
        session: AsyncSession,
        user: UserModel
) -> FileModel:

    saved_file = await save_file(file)
    db_file = FileModel(
        user_id=user.id,
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
        session: AsyncSession,
        user: UserModel
) -> None:
    db_file = await check_file_permission(file_id, session, user, allow_admin=False)

    try:
        os.remove(db_file.path)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(e)
        
    await session.delete(db_file)
    await session.commit()
    return


async def download_file(
        file_id: int,
        session: AsyncSession,
        user: UserModel
) -> FileResponse:
    db_file = await check_file_permission(file_id, session, user, allow_admin=False)

    return FileResponse(
        path=db_file.path,
        filename=db_file.filename,
        media_type='application/octet-stream'
    )

