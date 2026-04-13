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
    download_file
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
    return await get_files(db)


@router.get('/{file_id}', status_code=status.HTTP_200_OK, response_model=FileSchema)
async def get_file_endpoint(
        file_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    return await get_file(file_id, db, user)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=FileSchema)
async def create_file_endpoint(file: UploadFile = File(...),
                               db: AsyncSession = Depends(get_async_session),
                               user: UserModel = Depends(get_current_user)
):
    return await create_file(file, db, user)


@router.delete('/{file_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(
        file_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    await delete_file(file_id, db, user)


@router.get('/{file_id}/download', status_code=status.HTTP_200_OK, response_class=FileResponse)
async def download_file_endpoint(
        file_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    return await download_file(file_id, db, user)

