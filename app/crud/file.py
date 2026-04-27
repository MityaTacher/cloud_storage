import os
import uuid

from fastapi import HTTPException, status, UploadFile
from fastapi.responses import FileResponse

from sqlalchemy import Sequence, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FileModel, UserModel, DirectoryModel
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


async def check_directory_is_exist(
        dir_uid: uuid.UUID | None,
        user: UserModel,
        session: AsyncSession
) -> None:

    if dir_uid is None:
        return

    tmp = await session.scalars(
        select(DirectoryModel).
        where(DirectoryModel.uid == dir_uid)
    )
    db_dir: DirectoryModel = tmp.first()
    if db_dir is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Directory not found'
        )
    if db_dir.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You cannot perform this action'
        )


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
        user: UserModel,
        parent_uid: uuid.UUID | None
) -> FileModel:

    await check_directory_is_exist(parent_uid, user, session)

    saved_file = await save_file(file, parent_uid=parent_uid)
    db_file = FileModel(
        user_id=user.id,
        filename=saved_file.filename,
        path=saved_file.filepath,
        size_bytes=saved_file.size_bytes,
        parent_uid=saved_file.parent_uid
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


async def get_public_file(
    file_uid: uuid.UUID,
    session: AsyncSession
):
    tmp = await session.scalars(
        select(FileModel).
        where(FileModel.uid == file_uid).
        where(FileModel.access_level == 1)
    )
    db_file: FileModel = tmp.first()
    if db_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found'
        )
    return db_file


async def download_public_file(
        file_uid: uuid.UUID,
        session: AsyncSession
) -> FileResponse:

    tmp = await session.scalars(
        select(FileModel).
        where(FileModel.uid == file_uid)
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


async def generate_public_link(
        file: FileModel,
        session: AsyncSession
) -> uuid.UUID:
    link = uuid.uuid4()
    file.public_link = link
    file.access_level = 1
    await session.commit()
    return link


async def change_access_level(
        file_id: int,
        access_level: int,
        session: AsyncSession,
        user: UserModel
) -> str:
    db_file = await check_file_permission(file_id, session, user)

    match access_level:
        case 0:
            db_file.access_level = 0
            await session.commit()
            return 'public link is inactive'
        case 1:
            db_file.access_level = 1
            await session.commit()
            return str(db_file.uid)

    return 'unknown error'


