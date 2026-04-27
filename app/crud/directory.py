import uuid

from fastapi import HTTPException, status

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel, DirectoryModel, FileModel
from app.schemas import DirectorySchema


async def get_directory_with_relations(
        directory_uid: uuid.UUID,
        session: AsyncSession
) -> DirectoryModel:
    stmt = (
        select(DirectoryModel)
        .where(DirectoryModel.uid == directory_uid)
        .options(
            selectinload(DirectoryModel.children),
            selectinload(DirectoryModel.files)
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def check_directory_permission(
        directory_uid: uuid.UUID | None,
        session: AsyncSession,
        user: UserModel
) -> DirectorySchema:

    tmp = await session.scalars(
        select(DirectoryModel).
        where(DirectoryModel.uid == directory_uid).
        where(DirectoryModel.user_id == user.id)
        .options(
            selectinload(DirectoryModel.children),
            selectinload(DirectoryModel.files)
        )
    )
    db_directory = tmp.first()

    if db_directory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Directory not found'
        )
    return db_directory


async def check_directory_is_exist(
        dir_uid: uuid.UUID | None,
        user: UserModel,
        session: AsyncSession
) -> None:
    if dir_uid is None:
        return

    tmp = await session.scalars(
        select(DirectoryModel).
        where(DirectoryModel.uid == dir_uid)
    )
    db_dir: DirectoryModel = tmp.first()
    if db_dir is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Directory not found'
        )
    if db_dir.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You cannot perform this action'
        )


async def get_directory(
        directory_uid: uuid.UUID,
        session: AsyncSession,
        user: UserModel
) -> DirectorySchema:
    db_directory = await check_directory_permission(directory_uid, session, user)
    return db_directory


async def create_new_directory(
        parent_uid: uuid.UUID | None,
        name: str | None,
        user: UserModel,
        session: AsyncSession,
) -> DirectorySchema:
    await check_directory_is_exist(parent_uid, user, session)

    new_directory = DirectoryModel(
        name=name,
        user_id=user.id,
        parent_uid=parent_uid
    )
    session.add(new_directory)
    await session.commit()

    return await get_directory_with_relations(new_directory.uid, session)


async def delete_directory(
        directory_uid: uuid.UUID,
        session: AsyncSession,
        user: UserModel
) -> None:
    db_directory = await check_directory_permission(directory_uid, session, user)

    await session.delete(db_directory)
    await session.commit()


async def change_directory_access_level(
        directory_uid: uuid.UUID,
        access_level: int,
        session: AsyncSession,
        user: UserModel,
):
    db_directory = await check_directory_permission(directory_uid, session, user)

    cte = (
        select(DirectoryModel.uid)
        .where(DirectoryModel.uid == directory_uid)
        .cte(recursive=True)
    )

    cte = cte.union_all(
        select(DirectoryModel.uid)
        .where(DirectoryModel.parent_uid == cte.c.uid)
    )

    update_dirs_stmt = (
        update(DirectoryModel)
        .where(DirectoryModel.uid.in_(select(cte.c.uid)))
        .values(access_level=access_level)
    )

    update_files_stmt = (
        update(FileModel)
        .where(FileModel.parent_uid.in_(select(cte.c.uid)))
        .values(access_level=access_level)
    )

    await session.execute(update_dirs_stmt)
    await session.execute(update_files_stmt)
    await session.commit()

    return db_directory.public_link


async def get_public_directory(
        public_link: uuid.UUID,
        session: AsyncSession
):
    stmt = (
        select(DirectoryModel)
        .where(DirectoryModel.public_link == public_link)
        .where(DirectoryModel.access_level == 1)
        .options(
            selectinload(DirectoryModel.children),
            selectinload(DirectoryModel.files),
            with_loader_criteria(DirectoryModel, DirectoryModel.access_level == 1),
            with_loader_criteria(FileModel, FileModel.access_level == 1)
        )
    )

    result = await session.execute(stmt)
    db_directory = result.scalar_one_or_none()

    if db_directory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Directory not found'
        )
    return db_directory

