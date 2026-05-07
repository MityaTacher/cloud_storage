import uuid

from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi.responses import FileResponse

from app.db.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import FileSchema

from app.crud.file import (
    get_files,
    get_file,
    create_file,
    delete_file,
    download_file,
    change_access_level,
    download_public_file,
    get_public_file,
    move_file,
    save_public_file_to_cloud
)

from app.crud.user import get_current_user, get_current_admin
from app.models import UserModel

router = APIRouter(
    prefix='/files',
    tags=['Files'],
)

@router.get('/', status_code=status.HTTP_200_OK, response_model=list[FileSchema])
async def get_files_endpoint(
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_admin)
):
    """
    ADMIN ONLY
    возвращает все загруженные файлы
    """
    return await get_files(db)


@router.get('/{file_id}', status_code=status.HTTP_200_OK, response_model=FileSchema)
async def get_file_endpoint(
        file_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    OWNER ONLY
    по id файла в бд возвращает модель файла из бд
    """
    return await get_file(file_id, db, user)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=FileSchema)
async def create_file_endpoint(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user),
        parent_uid: uuid.UUID | None = None
):
    """
    AUTHORIZED ONLY
    Загружает файл и возращает модель из бд
    """
    return await create_file(file, db, user, parent_uid)


@router.delete('/{file_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(
        file_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    OWNER ONLY
    Удаляет файл по id
    """
    await delete_file(file_id, db, user)


@router.get('/{file_id}/download', status_code=status.HTTP_200_OK, response_class=FileResponse)
async def download_file_endpoint(
        file_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    OWNER ONLY
    Скачивает файл
    """
    return await download_file(file_id, db, user)


@router.get('/public/{uid}', status_code=status.HTTP_200_OK, response_model=FileSchema)
async def get_public_file_endpoint(
        uid: uuid.UUID,
        db: AsyncSession = Depends(get_async_session)
):
    """
    ANY USER
    Публичный доступ к файлу
    """
    return await get_public_file(uid, db)


@router.get('/public/{uid}/download', status_code=status.HTTP_200_OK, response_class=FileResponse)
async def download_public_file_endpoint(
        uid: uuid.UUID,
        db: AsyncSession = Depends(get_async_session)
):
    """
    ANY USER
    Скачивание файла любым пользователем
    """
    return await download_public_file(uid, db)


@router.patch('/{file_id}', status_code=status.HTTP_200_OK, response_model=str)
async def change_access_level_endpoint(
        file_id: int,
        access_level: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    USER ONLY
    поменять уровень доступа к файлу;
    1 - доступен всем по ссылке
    0 - доступен только владельцу
    """
    return await change_access_level(file_id, access_level, db, user)


@router.patch('/{file_id}/move', status_code=status.HTTP_200_OK, response_model=FileSchema)
async def move_file_endpoint(
        file_id: int,
        parent_uid: uuid.UUID | None = None,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    USER ONLY
    Переместить файл в другую директорию
    """
    return await move_file(file_id, parent_uid, db, user)


@router.post('/public/{uid}/save', status_code=status.HTTP_201_CREATED, response_model=FileSchema)
async def save_public_file_endpoint(
        uid: uuid.UUID,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    AUTHORIZED ONLY
    Сохранить публичный файл в свое облако (в корневую папку)
    """
    return await save_public_file_to_cloud(uid, db, user)