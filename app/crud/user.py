from fastapi import HTTPException, status

from sqlalchemy import select, or_, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel, FileModel
from app.schemas import UserSchema, UserCreate
from app.services.auth import (
    hash_password
)


async def get_users(
        session: AsyncSession
) -> Sequence[UserModel]:
    tmp = await session.scalars(select(UserModel))
    return tmp.all()


async def get_user(
        user_id: int,
        session: AsyncSession
) -> UserModel:
    tmp = await session.scalars(select(UserModel).where(UserModel.id == user_id))
    db_user = tmp.first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
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
        username=user.username
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def change_user_role():
    ...


async def delete_user(user_id: int, session: AsyncSession):
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
