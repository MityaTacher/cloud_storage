import uuid

from fastapi.params import Depends

from app.crud.user import get_current_user

from fastapi import status, APIRouter

from app.db.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel
from app.schemas import DirectorySchema

from app.crud.directory import create_new_directory, get_directory, delete_directory, change_directory_access_level, \
    get_public_directory

router = APIRouter(
    prefix='/folders',
    tags=['Folders']
)


@router.get('/{directory_uid}', status_code=status.HTTP_200_OK, response_model=DirectorySchema)
async def get_current_directory_endpoint(
        directory_uid: uuid.UUID,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    return await get_directory(directory_uid, db, user)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=DirectorySchema)
async def create_new_directory_endpoint(
        parent_uid: uuid.UUID | None = None,
        name: str | None = None,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
):
    """
    OWNER ONLY
    Просмотр параметров папки и ее содержимого
    """
    return await create_new_directory(parent_uid, name, user, session)


@router.put('/{directory_uid}', status_code=status.HTTP_200_OK, response_model=DirectorySchema)
async def change_directory_endpoint(
        name: str | None,
        parent_uid: uuid.UUID | None,
):
    return 'change'


@router.delete('/{directory_uid}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_directory_endpoint(
        directory_uid: uuid.UUID,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user),
):
    return await delete_directory(directory_uid, db, user)


@router.patch('/{directory_uid}', status_code=status.HTTP_200_OK)
async def change_access_level_endpoint(
        directory_uid: uuid.UUID,
        access_level: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    return await change_directory_access_level(directory_uid, access_level, db, user)


@router.get('/public/{public_link}', status_code=status.HTTP_200_OK)
async def get_public_directory_endpoint(
        public_link: uuid.UUID,
        db: AsyncSession = Depends(get_async_session)
):
    return await get_public_directory(public_link, db)
