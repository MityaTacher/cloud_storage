import uuid
import jwt
import httpx
from fastapi import HTTPException, status
from sqlalchemy import Sequence, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import FileModel, UserModel, DirectoryModel
from app.core.config import settings

async def check_file_permission(file_id: int, session: AsyncSession, user: UserModel, allow_admin: bool = False) -> FileModel:
    tmp = await session.scalars(select(FileModel).where(FileModel.id == file_id).options(selectinload(FileModel.node)))
    db_file = tmp.first()
    if db_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='File not found')
    if db_file.user_id != user.id and not (allow_admin and user.role == 'admin'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You cannot perform this action')
    return db_file

async def check_directory_is_exist(dir_uid: uuid.UUID | None, user: UserModel, session: AsyncSession) -> None:
    if dir_uid is None:
        return
    tmp = await session.scalars(select(DirectoryModel).where(DirectoryModel.uid == dir_uid))
    db_dir = tmp.first()
    if db_dir is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Directory not found')
    if db_dir.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You cannot perform this action')

async def get_files(session: AsyncSession) -> Sequence[FileModel]:
    tmp = await session.scalars(select(FileModel))
    return tmp.all()

async def get_file(file_id: int, session: AsyncSession, user: UserModel) -> FileModel:
    return await check_file_permission(file_id, session, user, allow_admin=True)

async def delete_file(file_id: int, session: AsyncSession, user: UserModel) -> None:
    db_file = await check_file_permission(file_id, session, user, allow_admin=False)
    
    if db_file.node:
        token = jwt.encode({"action": "delete", "path": db_file.path}, settings.cluster_secret, algorithm="HS256")
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(f"{db_file.node.internal_address}/api/storage/delete?token={token}")
        except Exception as e:
            print(f"Failed to delete file from storage node: {e}")

    await session.delete(db_file)
    await session.commit()

async def get_public_file(file_uid: uuid.UUID, session: AsyncSession):
    tmp = await session.scalars(select(FileModel).where(FileModel.uid == file_uid).where(FileModel.access_level == 1))
    db_file = tmp.first()
    if db_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='File not found')
    return db_file

async def change_access_level(file_id: int, access_level: int, session: AsyncSession, user: UserModel) -> str:
    db_file = await check_file_permission(file_id, session, user)
    db_file.access_level = access_level
    await session.commit()
    return str(db_file.uid) if access_level == 1 else 'public link is inactive'

async def move_file(file_id: int, parent_uid: uuid.UUID | None, session: AsyncSession, user: UserModel) -> FileModel:
    db_file = await check_file_permission(file_id, session, user)
    await check_directory_is_exist(parent_uid, user, session)
    
    db_file.parent_uid = parent_uid
    if parent_uid:
        parent_dir = (await session.scalars(select(DirectoryModel).where(DirectoryModel.uid == parent_uid))).first()
        if parent_dir:
            db_file.access_level = parent_dir.access_level
    else:
        db_file.access_level = 0 

    await session.commit()
    await session.refresh(db_file)
    return db_file

async def save_public_file_to_cloud(file_uid: uuid.UUID, session: AsyncSession, user: UserModel) -> FileModel:
    db_file = (await session.scalars(select(FileModel).where(FileModel.uid == file_uid).where(FileModel.access_level == 1).options(selectinload(FileModel.node)))).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    existing_file = (await session.scalars(select(FileModel).where(FileModel.user_id == user.id).where(FileModel.parent_uid.is_(None)).where(FileModel.filename == db_file.filename))).first()
    if existing_file:
        raise HTTPException(status_code=409, detail=f'File "{db_file.filename}" already saved to your My Cloud')
    
    new_path = str(uuid.uuid4())
    token = jwt.encode({"action": "copy", "src_path": db_file.path, "dest_path": new_path}, settings.cluster_secret, algorithm="HS256")
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{db_file.node.internal_address}/api/storage/internal/copy?token={token}")
            res.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage node error: {e}")

    new_db_file = FileModel(
        user_id=user.id, filename=db_file.filename, path=new_path, size_bytes=db_file.size_bytes,
        parent_uid=None, access_level=0, status="READY", node_id=db_file.node_id
    )
    session.add(new_db_file)
    await session.commit()
    await session.refresh(new_db_file)
    return new_db_file

async def rename_file(file_id: int, new_name: str, session: AsyncSession, user: UserModel) -> FileModel:
    db_file = await check_file_permission(file_id, session, user)
    db_file.filename = new_name
    await session.commit()
    await session.refresh(db_file)
    return db_file
