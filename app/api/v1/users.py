from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas import UserSchema, UserCreate, FileSchema, RefreshTokenRequest
from app.models import UserModel

from app.crud.user import (
    get_users,
    get_user_by_id,
    get_user_files,
    create_user,
    change_user_role,
    delete_user,
    login,
    refresh,
    get_current_user,
    get_current_admin,
    check_user_permissions
)



router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.post('/token')
async def login_endpoint(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_session)):
    return await login(form_data, db)


@router.post('/refresh')
async def refresh_token_endpoint(
        body: RefreshTokenRequest,
        db: AsyncSession = Depends(get_async_session)
):
    return await refresh(body.token, db)


@router.get('/', status_code=status.HTTP_200_OK, response_model=list[UserSchema])
async def get_users_endpoint(
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_admin),
):
    return await get_users(db)


@router.get('/{user_id}', status_code=status.HTTP_200_OK, response_model=UserSchema)
async def get_user_endpoint(
        user_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):

    await check_user_permissions(user_id, user, allow_admin=True)

    return await get_user_by_id(user_id, db)


@router.get('/{user_id}/files', status_code=status.HTTP_200_OK, response_model=list[FileSchema])
async def get_user_files_endpoint(
        user_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    await check_user_permissions(user_id, user, allow_admin=True)

    return await get_user_files(user_id, db)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def create_user_endpoint(
        user: UserCreate,
        db: AsyncSession = Depends(get_async_session)
):
    return await create_user(user, db)


@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
        user_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    await check_user_permissions(user_id, user, allow_admin=True)

    await delete_user(user_id, db, user)

#TODO update endpoints
