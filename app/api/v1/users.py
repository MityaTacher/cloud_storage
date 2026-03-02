from http.client import HTTPException

from fastapi import APIRouter, status, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas import UserSchema, UserCreate, FileSchema

from app.crud.user import (
    get_users,
    get_user,
    get_user_files,
    create_user,
    change_user_role,
    delete_user,
)

router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.get('/', status_code=status.HTTP_200_OK, response_model=list[UserSchema])
async def get_users_endpoint(db: AsyncSession = Depends(get_async_session)):
    return await get_users(db)


@router.get('/{user_id}', status_code=status.HTTP_200_OK, response_model=UserSchema)
async def get_user_endpoint(user_id: int, db: AsyncSession = Depends(get_async_session)):
    return await get_user(user_id, db)


@router.get('/{user_id}/files', status_code=status.HTTP_200_OK, response_model=list[FileSchema])
async def get_user_files_endpoint(user_id: int, db: AsyncSession = Depends(get_async_session)):
    return await get_user_files(user_id, db)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def create_user_endpoint(user: UserCreate, db: AsyncSession = Depends(get_async_session)):
    return await create_user(user, db)


@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(user_id: int, db: AsyncSession = Depends(get_async_session)):
    await delete_user(user_id, db)

#TODO update endpoints
