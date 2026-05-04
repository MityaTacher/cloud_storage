import os
import uuid
import shutil

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

    # Проверка на существование файла с таким же именем в текущей папке
    existing_file = await session.scalars(
        select(FileModel)
        .where(FileModel.user_id == user.id)
        .where(FileModel.parent_uid == parent_uid)
        .where(FileModel.filename == file.filename)
    )
    if existing_file.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'File "{file.filename}" already exists in this folder'
        )

    parent_access = 0
    if parent_uid:
        tmp = await session.scalars(
            select(DirectoryModel).where(DirectoryModel.uid == parent_uid)
        )
        parent_dir = tmp.first()
        if parent_dir:
            parent_access = parent_dir.access_level

    saved_file = await save_file(file, parent_uid=parent_uid)
    db_file = FileModel(
        user_id=user.id,
        filename=saved_file.filename,
        path=saved_file.filepath,
        size_bytes=saved_file.size_bytes,
        parent_uid=saved_file.parent_uid,
        access_level=parent_access,
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
        select(FileModel)
        .where(FileModel.uid == file_uid)
        .where(FileModel.access_level == 1)
    )
    db_file = tmp.first()
    if db_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found or not public'
        )

    return FileResponse(
        path=db_file.path,
        filename=db_file.filename,
        media_type='application/octet-stream'
    )


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


async def move_file(
        file_id: int,
        parent_uid: uuid.UUID | None,
        session: AsyncSession,
        user: UserModel
) -> FileModel:
    db_file = await check_file_permission(file_id, session, user)
    await check_directory_is_exist(parent_uid, user, session)
    
    db_file.parent_uid = parent_uid
    
    if parent_uid:
        tmp = await session.scalars(select(DirectoryModel).where(DirectoryModel.uid == parent_uid))
        parent_dir = tmp.first()
        if parent_dir:
            db_file.access_level = parent_dir.access_level
    else:
        db_file.access_level = 0 

    await session.commit()
    await session.refresh(db_file)
    return db_file


async def save_public_file_to_cloud(
        file_uid: uuid.UUID,
        session: AsyncSession,
        user: UserModel
) -> FileModel:
    from app.core.config import settings
    
    db_file = await get_public_file(file_uid, session)
    
    existing_file = await session.scalars(
        select(FileModel)
        .where(FileModel.user_id == user.id)
        .where(FileModel.parent_uid.is_(None))
        .where(FileModel.filename == db_file.filename)
    )
    if existing_file.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'File "{db_file.filename}" already saved to your My Cloud'
        )
    
    new_safe_name = f"{uuid.uuid4()}_{db_file.filename}"
    new_filepath = os.path.join(settings.upload_dir, new_safe_name)
    shutil.copy2(db_file.path, new_filepath)
    
    new_db_file = FileModel(
        user_id=user.id,
        filename=db_file.filename,
        path=new_filepath,
        size_bytes=db_file.size_bytes,
        parent_uid=None,
        access_level=0 
    )
    session.add(new_db_file)
    await session.commit()
    await session.refresh(new_db_file)
    return new_db_file


async def rename_file(
        file_id: int,
        new_name: str,
        session: AsyncSession,
        user: UserModel
) -> FileModel:
    db_file = await check_file_permission(file_id, session, user)
    
    existing_file = await session.scalars(
        select(FileModel)
        .where(FileModel.user_id == user.id)
        .where(FileModel.parent_uid == db_file.parent_uid)
        .where(FileModel.filename == new_name)
    )
    if existing_file.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'File "{new_name}" already exists in this folder'
        )
        
    db_file.filename = new_name
    await session.commit()
    await session.refresh(db_file)
    return db_file