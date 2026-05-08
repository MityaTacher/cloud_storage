import os
import uuid
from fastapi import status, APIRouter, BackgroundTasks
from fastapi.params import Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.crud.user import get_current_user
from app.models import UserModel
from app.schemas import DirectorySchema

from app.crud.directory import (
    create_new_directory, 
    get_directory, 
    delete_directory, 
    change_directory_access_level, 
    get_public_directory,
    save_public_directory_to_cloud,
    generate_directory_zip,
    rename_directory
)

router = APIRouter(
    prefix='/v1/folders',
    tags=['Folders']
)

@router.get('/{directory_uid}', status_code=status.HTTP_200_OK, response_model=DirectorySchema)
async def get_current_directory_endpoint(directory_uid: uuid.UUID, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await get_directory(directory_uid, db, user)

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=DirectorySchema)
async def create_new_directory_endpoint(parent_uid: uuid.UUID | None = None, name: str | None = None, user: UserModel = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    return await create_new_directory(parent_uid, name, user, session)

@router.delete('/{directory_uid}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_directory_endpoint(directory_uid: uuid.UUID, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await delete_directory(directory_uid, db, user)

@router.patch('/{directory_uid}', status_code=status.HTTP_200_OK)
async def change_access_level_endpoint(directory_uid: uuid.UUID, access_level: int, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await change_directory_access_level(directory_uid, access_level, db, user)

@router.get('/public/{public_link}', status_code=status.HTTP_200_OK)
async def get_public_directory_endpoint(public_link: uuid.UUID, db: AsyncSession = Depends(get_async_session)):
    return await get_public_directory(public_link, db)

@router.post('/public/{public_link}/save', status_code=status.HTTP_201_CREATED, response_model=DirectorySchema)
async def save_public_directory_endpoint(public_link: uuid.UUID, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await save_public_directory_to_cloud(public_link, db, user)

@router.get('/{directory_uid}/download', status_code=status.HTTP_200_OK, response_class=FileResponse)
async def download_directory_endpoint(directory_uid: uuid.UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    temp_path, dir_name = await generate_directory_zip(directory_uid, db, user=user)
    background_tasks.add_task(os.remove, temp_path)
    return FileResponse(path=temp_path, filename=f"{dir_name}.zip", media_type='application/zip')

@router.get('/public/{public_link}/download', status_code=status.HTTP_200_OK, response_class=FileResponse)
async def download_public_directory_endpoint(public_link: uuid.UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_async_session)):
    temp_path, dir_name = await generate_directory_zip(public_link, db, is_public=True)
    background_tasks.add_task(os.remove, temp_path)
    return FileResponse(path=temp_path, filename=f"{dir_name}.zip", media_type='application/zip')

@router.patch('/{directory_uid}/rename', status_code=status.HTTP_200_OK, response_model=DirectorySchema)
async def rename_directory_endpoint(directory_uid: uuid.UUID, new_name: str, db: AsyncSession = Depends(get_async_session), user: UserModel = Depends(get_current_user)):
    return await rename_directory(directory_uid, new_name, db, user)
