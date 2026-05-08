import uuid
import jwt
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_async_session
from app.schemas import FileSchema
from app.models import UserModel, FileModel, StorageNodeModel, DirectoryModel

from app.crud.file import (
    get_files,
    get_file,
    delete_file,
    change_access_level,
    get_public_file,
    move_file,
    save_public_file_to_cloud,
    check_directory_is_exist,
    rename_file
)
from app.crud.user import get_current_user, get_current_admin

router = APIRouter(
    prefix='/v1/files',
    tags=['Files'],
)

@router.get('/', status_code=status.HTTP_200_OK, response_model=list[FileSchema])
async def get_files_endpoint(db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_admin)):
    return await get_files(db)

@router.get('/{file_id}', status_code=status.HTTP_200_OK, response_model=FileSchema)
async def get_file_endpoint(file_id: int, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await get_file(file_id, db, user)

@router.post('/upload-request', status_code=status.HTTP_200_OK)
async def request_file_upload(
        filename: str,
        size_bytes: int,
        parent_uid: uuid.UUID | None = None,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    await check_directory_is_exist(parent_uid, user, db)

    node = (await db.scalars(select(StorageNodeModel).where(StorageNodeModel.free_space_bytes > size_bytes).order_by(StorageNodeModel.free_space_bytes.desc()))).first()
    if not node:
        raise HTTPException(status_code=507, detail="No storage nodes available or insufficient space")

    # Наследование прав от родительской папки
    access_level = 0
    if parent_uid:
        parent_dir = (await db.scalars(select(DirectoryModel).where(DirectoryModel.uid == parent_uid))).first()
        if parent_dir:
            access_level = parent_dir.access_level

    new_file = FileModel(
        user_id=user.id,
        filename=filename,
        path=str(uuid.uuid4()),
        size_bytes=size_bytes,
        parent_uid=parent_uid,
        status="PENDING",
        node_id=node.id,
        access_level=access_level
    )
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)

    token = jwt.encode({"action": "upload", "file_id": new_file.id, "path": new_file.path}, settings.cluster_secret, algorithm="HS256")
    
    return {
        "file_id": new_file.id,
        "upload_url": f"{node.address}/api/storage/upload",
        "token": token
    }

@router.delete('/{file_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(file_id: int, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    await delete_file(file_id, db, user)

@router.get('/{file_id}/download', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def download_file_endpoint(file_id: int, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    db_file = (await db.scalars(select(FileModel).where(FileModel.id == file_id).options(selectinload(FileModel.node)))).first()
    if not db_file or db_file.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if db_file.status != "READY":
        raise HTTPException(status_code=400, detail="File is not ready")

    token = jwt.encode({"action": "download", "path": db_file.path, "filename": db_file.filename}, settings.cluster_secret, algorithm="HS256")
    return RedirectResponse(url=f"{db_file.node.address}/api/storage/download?token={token}")

@router.get('/public/{uid}', status_code=status.HTTP_200_OK, response_model=FileSchema)
async def get_public_file_endpoint(uid: uuid.UUID, db: AsyncSession = Depends(get_async_session)):
    return await get_public_file(uid, db)

@router.get('/public/{uid}/download', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def download_public_file_endpoint(uid: uuid.UUID, db: AsyncSession = Depends(get_async_session)):
    db_file = (await db.scalars(select(FileModel).where(FileModel.uid == uid).where(FileModel.access_level == 1).options(selectinload(FileModel.node)))).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found or not public")
    if db_file.status != "READY":
        raise HTTPException(status_code=400, detail="File is not ready")

    token = jwt.encode({"action": "download", "path": db_file.path, "filename": db_file.filename}, settings.cluster_secret, algorithm="HS256")
    return RedirectResponse(url=f"{db_file.node.address}/api/storage/download?token={token}")

@router.patch('/{file_id}', status_code=status.HTTP_200_OK, response_model=str)
async def change_access_level_endpoint(file_id: int, access_level: int, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await change_access_level(file_id, access_level, db, user)

@router.patch('/{file_id}/move', status_code=status.HTTP_200_OK, response_model=FileSchema)
async def move_file_endpoint(file_id: int, parent_uid: uuid.UUID | None = None, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await move_file(file_id, parent_uid, db, user)

@router.patch('/{file_id}/rename', status_code=status.HTTP_200_OK, response_model=FileSchema)
async def rename_file_endpoint(file_id: int, new_name: str, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await rename_file(file_id, new_name, db, user)

@router.post('/public/{uid}/save', status_code=status.HTTP_201_CREATED, response_model=FileSchema)
async def save_public_file_endpoint(uid: uuid.UUID, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await save_public_file_to_cloud(uid, db, user)
