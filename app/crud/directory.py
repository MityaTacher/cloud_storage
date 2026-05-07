import os
import shutil
import uuid
import zipfile
import tempfile

from fastapi import HTTPException, status

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel, DirectoryModel, FileModel
from app.schemas import DirectorySchema
from app.core.config import settings


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

    existing_dir = await session.scalars(
        select(DirectoryModel)
        .where(DirectoryModel.user_id == user.id)
        .where(DirectoryModel.parent_uid == parent_uid)
        .where(DirectoryModel.name == name)
    )
    if existing_dir.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Folder "{name}" already exists'
        )

    new_directory = DirectoryModel(
        name=name,
        user_id=user.id,
        parent_uid=parent_uid
    )
    session.add(new_directory)
    await session.commit()

    return await get_directory_with_relations(new_directory.uid, session)


async def _delete_directory_files_recursively(dir_uid: uuid.UUID, session: AsyncSession):
    """
    Рекурсивно обходит все подпапки и удаляет физические файлы с жесткого диска.
    """
    stmt = (
        select(DirectoryModel)
        .where(DirectoryModel.uid == dir_uid)
        .options(
            selectinload(DirectoryModel.files),
            selectinload(DirectoryModel.children)
        )
    )
    dir_obj = (await session.scalars(stmt)).first()
    
    if not dir_obj:
        return

    for f in dir_obj.files:
        try:
            if os.path.exists(f.path):
                os.remove(f.path)
        except Exception as e:
            print(f"Ошибка при удалении файла {f.path}: {e}")

    for child in dir_obj.children:
        await _delete_directory_files_recursively(child.uid, session)


async def delete_directory(
        directory_uid: uuid.UUID,
        session: AsyncSession,
        user: UserModel
) -> None:
    db_directory = await check_directory_permission(directory_uid, session, user)

    await _delete_directory_files_recursively(directory_uid, session)

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

    if access_level == 1:
        await session.execute(update_files_stmt)

    await session.commit()

    await session.refresh(db_directory)
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


async def _copy_tree(src_uid: uuid.UUID, dest_parent_uid: uuid.UUID | None, session: AsyncSession, user: UserModel) -> DirectoryModel | None:
    stmt = select(DirectoryModel).where(DirectoryModel.uid == src_uid).where(DirectoryModel.access_level == 1)
    dir_obj = (await session.scalars(stmt)).first()
    if not dir_obj: 
        return None
    
    new_dir = DirectoryModel(name=dir_obj.name, user_id=user.id, parent_uid=dest_parent_uid, access_level=0)
    session.add(new_dir)
    await session.flush()
    
    stmt_files = select(FileModel).where(FileModel.parent_uid == src_uid).where(FileModel.access_level == 1)
    files = (await session.scalars(stmt_files)).all()
    for f in files:
        new_safe_name = f"{uuid.uuid4()}_{f.filename}"
        new_filepath = os.path.join(settings.upload_dir, new_safe_name)
        try:
            shutil.copy2(f.path, new_filepath)
        except FileNotFoundError:
            continue
        new_f = FileModel(
            user_id=user.id, 
            filename=f.filename, 
            path=new_filepath, 
            size_bytes=f.size_bytes, 
            parent_uid=new_dir.uid, 
            access_level=0
        )
        session.add(new_f)
    
    stmt_dirs = select(DirectoryModel).where(DirectoryModel.parent_uid == src_uid).where(DirectoryModel.access_level == 1)
    subdirs = (await session.scalars(stmt_dirs)).all()
    for child in subdirs:
        await _copy_tree(child.uid, new_dir.uid, session, user)
        
    return new_dir


async def save_public_directory_to_cloud(
        public_link: uuid.UUID,
        session: AsyncSession,
        user: UserModel
) -> DirectorySchema:
    db_dir = await get_public_directory(public_link, session)
    
    existing_dir = await session.scalars(
        select(DirectoryModel)
        .where(DirectoryModel.user_id == user.id)
        .where(DirectoryModel.parent_uid.is_(None))
        .where(DirectoryModel.name == db_dir.name)
    )
    if existing_dir.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Folder "{db_dir.name}" already saved to your My Cloud'
        )
        
    new_dir = await _copy_tree(db_dir.uid, None, session, user)
    await session.commit()
    
    return await get_directory_with_relations(new_dir.uid, session)


async def _gather_files_for_zip(
    dir_uid: uuid.UUID, 
    current_path: str, 
    session: AsyncSession, 
    files_list: list,
    is_public: bool = False
):
    stmt = select(DirectoryModel).where(DirectoryModel.uid == dir_uid)
    if is_public:
        stmt = stmt.where(DirectoryModel.access_level == 1)
        
    stmt = stmt.options(selectinload(DirectoryModel.files), selectinload(DirectoryModel.children))
    dir_obj = (await session.scalars(stmt)).first()
    
    if not dir_obj:
        return

    for f in dir_obj.files:
        if not is_public or f.access_level == 1:
            files_list.append((f.path, os.path.join(current_path, f.filename)))
    
    for child in dir_obj.children:
        if not is_public or child.access_level == 1:
            await _gather_files_for_zip(
                child.uid, 
                os.path.join(current_path, child.name), 
                session, 
                files_list, 
                is_public
            )


async def generate_directory_zip(
        directory_uid: uuid.UUID,
        session: AsyncSession,
        user: UserModel | None = None,
        is_public: bool = False
) -> tuple[str, str]:
    if is_public:
        db_dir = await get_public_directory(directory_uid, session)
    else:
        if not user:
            raise HTTPException(status_code=403)
        db_dir = await check_directory_permission(directory_uid, session, user)

    files_to_zip = []
    await _gather_files_for_zip(db_dir.uid, db_dir.name, session, files_to_zip, is_public=is_public)

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_zip_path = temp_zip.name
    temp_zip.close()

    with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for physical_path, archive_path in files_to_zip:
            if os.path.exists(physical_path):
                zipf.write(physical_path, archive_path)

    return temp_zip_path, db_dir.name