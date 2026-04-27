import uuid

from fastapi import HTTPException, status, Depends

from sqlalchemy import select, or_, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import UserModel, FileModel, TokenModel, DirectoryModel
from app.schemas import UserCreate, DirectoryRoot
from app.services.auth import (
    hash_password,
    decode_token
)
from fastapi.security import OAuth2PasswordRequestForm

from datetime import datetime, timedelta, UTC
from app.core.config import settings
from app.db.session import get_async_session

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_token,
    verify_token,
    oauth2_scheme
)
from uuid import uuid4

async def check_user_permissions(
        user_id: int,
        user: UserModel,
        allow_admin: bool = False
) -> None:
    if user_id != user.id and not (allow_admin and user.role == 'admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You cannot perform this action'
        )


async def create_session_tokens(user_id: int, user_role: str, session: AsyncSession) -> dict:
    time_now = datetime.now(tz=UTC)
    exp_access = time_now + timedelta(minutes=settings.access_token_expires_minutes)
    exp_refresh = time_now + timedelta(days=settings.refresh_token_expires_days)

    access_token = create_access_token({
        'sub': str(user_id),
        'iat': time_now,
        'role': user_role,
        'exp': exp_access
    })

    token_uuid = str(uuid4())
    refresh_token = create_refresh_token({
        'sub': str(user_id),
        'iat': time_now,
        'jti': token_uuid,
        'exp': exp_refresh
    })

    db_token = TokenModel(
        user_id=user_id,
        hashed_token=hash_token(refresh_token),
        expires_at=exp_refresh,
        jti=token_uuid
    )
    session.add(db_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


async def login(form_data: OAuth2PasswordRequestForm, session: AsyncSession):
    result = await session.execute(
        select(UserModel).where(
            or_(UserModel.email == form_data.username, UserModel.username == form_data.username)
        )
    )
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    tokens = await create_session_tokens(db_user.id, db_user.role, session)
    await session.commit()
    return tokens


async def refresh(token: str, session: AsyncSession) -> dict:
    payload = decode_token(token, expected_type='refresh')

    result = await session.execute(
        select(TokenModel)
        .options(joinedload(TokenModel.user))
        .where(TokenModel.jti == payload.jti)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.revoked or not verify_token(token, db_token.hashed_token):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    await session.delete(db_token)

    user = db_token.user
    tokens = await create_session_tokens(user.id, user.role, session)

    await session.commit()
    return tokens


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_async_session)
) -> UserModel:
    payload = decode_token(token, 'access')
    user = await get_user_by_id(int(payload.sub), session)
    return user


async def get_current_admin(
        user: UserModel = Depends(get_current_user)
) -> UserModel:
    if user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You cannot perform this action'
        )
    return user


async def get_users(
        session: AsyncSession
) -> Sequence[UserModel]:
    tmp = await session.scalars(select(UserModel))
    return tmp.all()


async def get_user_by_id(
        user_id: int,
        session: AsyncSession
) -> UserModel:
    tmp = await session.scalars(select(UserModel).where(UserModel.id == user_id))
    db_user = tmp.first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return db_user


async def get_user_files(
        user_id: int,
        session: AsyncSession
) -> Sequence[FileModel]:
    tmp = await session.scalars(
        select(FileModel)
        .where(FileModel.user_id == user_id)
    )
    return tmp.all()


async def get_root(
        session: AsyncSession,
        user: UserModel
) -> DirectoryRoot:
    tmp = await session.scalars(
        select(DirectoryModel)
        .where(DirectoryModel.user_id == user.id)
        .where(DirectoryModel.parent_uid.is_(None))
    )
    res_directories = list(tmp.all())
    tmp1 = await session.scalars(
        select(FileModel)
        .where(FileModel.user_id == user.id)
        .where(FileModel.parent_uid.is_(None))
    )
    res_files = list(tmp1.all())
    return DirectoryRoot(children=res_directories, files=res_files)



async def create_user(
        user: UserCreate,
        session: AsyncSession,
) -> UserModel:
    tmp = await session.scalars(select(UserModel)
    .where(
        or_(
            UserModel.email == user.email,
            UserModel.username == user.username,
            )
        )
    )
    for db_user in tmp.all():
        if db_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='User with the specified email address already exists.'
            )
        if db_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='User with the specified username address already exists.'
            )

    new_user = UserModel(
        email=user.email,
        hashed_password=hash_password(user.password.get_secret_value()),
        username=user.username,
        role='user'
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def change_user_role():
    ...


async def delete_user(
        user_id: int,
        session: AsyncSession,
        user: UserModel
):
    tmp = await session.scalars(
        select(UserModel)
        .where(UserModel.id == user_id)
    )
    db_user = tmp.first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    await session.delete(db_user)
    await session.commit()

