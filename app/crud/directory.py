import os
import uuid
import zipfile
import tempfile
import httpx
import jwt

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel, DirectoryModel, FileModel
from app.schemas import DirectorySchema
from app.core.config import settings

async def get_directory_with_relations(directory_uid: uuid.UUID, session: AsyncSession) -> DirectoryModel:
    stmt = select(DirectoryModel).where(DirectoryModel.uid == directory_uid).options(selectinload(DirectoryModel.children), selectinload(DirectoryModel.files))
    return (await session.execute(stmt)).scalar_one()

async def check_directory_permission(directory_uid: uuid.UUID | None, session: AsyncSession, user: UserModel) -> DirectorySchema:
    db_directory = (await session.scalars(select(DirectoryModel).where(DirectoryModel.uid == directory_uid).where(DirectoryModel.user_id == user.id).options(selectinload(DirectoryModel.children), selectinload(DirectoryModel.files)))).first()
    if not db_directory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Directory not found')
    return db_directory

async def check_directory_is_exist(dir_uid: uuid.UUID | None, user: UserModel, session: AsyncSession) -> None:
    if dir_uid is None: return
    db_dir = (await session.scalars(select(DirectoryModel).where(DirectoryModel.uid == dir_uid))).first()
    if not db_dir: raise HTTPException(status_code=404, detail='Directory not found')
    if db_dir.user_id != user.id: raise HTTPException(status_code=403, detail='You cannot perform this action')

async def get_directory(directory_uid: uuid.UUID, session: AsyncSession, user: UserModel) -> DirectorySchema:
    return await check_directory_permission(directory_uid, session, user)

async def create_new_directory(parent_uid: uuid.UUID | None, name: str | None, user: UserModel, session: AsyncSession) -> DirectorySchema:
    await check_directory_is_exist(parent_uid, user, session)
    existing_dir = (await session.scalars(select(DirectoryModel).where(DirectoryModel.user_id == user.id).where(DirectoryModel.parent_uid == parent_uid).where(DirectoryModel.name == name))).first()
    if existing_dir: raise HTTPException(status_code=409, detail=f'Folder "{name}" already exists')

    # Наследование прав от родителя
    access_level = 0
    if parent_uid:
        parent_dir = (await session.scalars(select(DirectoryModel).where(DirectoryModel.uid == parent_uid))).first()
        if parent_dir:
            access_level = parent_dir.access_level

    new_directory = DirectoryModel(name=name, user_id=user.id, parent_uid=parent_uid, access_level=access_level)
    session.add(new_directory)
    await session.commit()
    return await get_directory_with_relations(new_directory.uid, session)

async def _delete_directory_files_recursively(dir_uid: uuid.UUID, session: AsyncSession):
    dir_obj = (await session.scalars(select(DirectoryModel).where(DirectoryModel.uid == dir_uid).options(selectinload(DirectoryModel.files).selectinload(FileModel.node), selectinload(DirectoryModel.children)))).first()
    if not dir_obj: return

    for f in dir_obj.files:
        if f.node:
            token = jwt.encode({"action": "delete", "path": f.path}, settings.cluster_secret, algorithm="HS256")
            try:
                async with httpx.AsyncClient() as client:
                    await client.delete(f"{f.node.internal_address}/api/storage/delete?token={token}")
            except Exception:
                pass

    for child in dir_obj.children:
        await _delete_directory_files_recursively(child.uid, session)

async def delete_directory(directory_uid: uuid.UUID, session: AsyncSession, user: UserModel) -> None:
    db_directory = await check_directory_permission(directory_uid, session, user)
    await _delete_directory_files_recursively(directory_uid, session)
    await session.delete(db_directory)
    await session.commit()

async def change_directory_access_level(directory_uid: uuid.UUID, access_level: int, session: AsyncSession, user: UserModel):
    db_directory = await check_directory_permission(directory_uid, session, user)
    cte = select(DirectoryModel.uid).where(DirectoryModel.uid == directory_uid).cte(recursive=True)
    cte = cte.union_all(select(DirectoryModel.uid).where(DirectoryModel.parent_uid == cte.c.uid))
    await session.execute(update(DirectoryModel).where(DirectoryModel.uid.in_(select(cte.c.uid))).values(access_level=access_level))
    if access_level == 1:
        await session.execute(update(FileModel).where(FileModel.parent_uid.in_(select(cte.c.uid))).values(access_level=access_level))
    await session.commit()
    await session.refresh(db_directory)
    return db_directory.public_link

async def get_public_directory(public_link: uuid.UUID, session: AsyncSession):
    stmt = select(DirectoryModel).where(DirectoryModel.public_link == public_link).where(DirectoryModel.access_level == 1).options(
        selectinload(DirectoryModel.children), selectinload(DirectoryModel.files),
        with_loader_criteria(DirectoryModel, DirectoryModel.access_level == 1),
        with_loader_criteria(FileModel, FileModel.access_level == 1)
    )
    db_directory = (await session.execute(stmt)).scalar_one_or_none()
    if not db_directory: raise HTTPException(status_code=404, detail='Directory not found')
    return db_directory

async def _copy_tree(src_uid: uuid.UUID, dest_parent_uid: uuid.UUID | None, session: AsyncSession, user: UserModel) -> DirectoryModel | None:
    dir_obj = (await session.scalars(select(DirectoryModel).where(DirectoryModel.uid == src_uid).where(DirectoryModel.access_level == 1))).first()
    if not dir_obj: return None
    
    new_dir = DirectoryModel(name=dir_obj.name, user_id=user.id, parent_uid=dest_parent_uid, access_level=0)
    session.add(new_dir)
    await session.flush()
    
    files = (await session.scalars(select(FileModel).where(FileModel.parent_uid == src_uid).where(FileModel.access_level == 1).options(selectinload(FileModel.node)))).all()
    for f in files:
        new_path = str(uuid.uuid4())
        token = jwt.encode({"action": "copy", "src_path": f.path, "dest_path": new_path}, settings.cluster_secret, algorithm="HS256")
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{f.node.internal_address}/api/storage/internal/copy?token={token}")
                res.raise_for_status()
            session.add(FileModel(user_id=user.id, filename=f.filename, path=new_path, size_bytes=f.size_bytes, parent_uid=new_dir.uid, access_level=0, status="READY", node_id=f.node_id))
        except Exception:
            continue
    
    subdirs = (await session.scalars(select(DirectoryModel).where(DirectoryModel.parent_uid == src_uid).where(DirectoryModel.access_level == 1))).all()
    for child in subdirs: await _copy_tree(child.uid, new_dir.uid, session, user)
    return new_dir

async def save_public_directory_to_cloud(public_link: uuid.UUID, session: AsyncSession, user: UserModel) -> DirectorySchema:
    db_dir = await get_public_directory(public_link, session)
    if (await session.scalars(select(DirectoryModel).where(DirectoryModel.user_id == user.id).where(DirectoryModel.parent_uid.is_(None)).where(DirectoryModel.name == db_dir.name))).first():
        raise HTTPException(status_code=409, detail=f'Folder "{db_dir.name}" already saved to your My Cloud')
    new_dir = await _copy_tree(db_dir.uid, None, session, user)
    await session.commit()
    return await get_directory_with_relations(new_dir.uid, session)

async def _gather_files_for_zip(dir_uid: uuid.UUID, current_path: str, session: AsyncSession, files_list: list, is_public: bool = False):
    stmt = select(DirectoryModel).where(DirectoryModel.uid == dir_uid)
    if is_public: stmt = stmt.where(DirectoryModel.access_level == 1)
    dir_obj = (await session.scalars(stmt.options(selectinload(DirectoryModel.files).selectinload(FileModel.node), selectinload(DirectoryModel.children)))).first()
    if not dir_obj: return

    for f in dir_obj.files:
        if f.status == "READY" and (not is_public or f.access_level == 1):
            files_list.append({"node_address": f.node.internal_address, "storage_path": f.path, "archive_path": os.path.join(current_path, f.filename)})
    for child in dir_obj.children:
        if not is_public or child.access_level == 1:
            await _gather_files_for_zip(child.uid, os.path.join(current_path, child.name), session, files_list, is_public)

async def generate_directory_zip(directory_uid: uuid.UUID, session: AsyncSession, user: UserModel | None = None, is_public: bool = False) -> tuple[str, str]:
    db_dir = await get_public_directory(directory_uid, session) if is_public else await check_directory_permission(directory_uid, session, user)
    files_to_zip = []
    await _gather_files_for_zip(db_dir.uid, db_dir.name, session, files_to_zip, is_public=is_public)

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_dir = tempfile.mkdtemp()

    with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        async with httpx.AsyncClient() as client:
            for f in files_to_zip:
                token = jwt.encode({"action": "internal_download", "path": f["storage_path"]}, settings.cluster_secret, algorithm="HS256")
                tmp_file_path = os.path.join(temp_dir, str(uuid.uuid4()))
                try:
                    async with client.stream('GET', f"{f['node_address']}/api/storage/internal/download?token={token}") as response:
                        if response.status_code == 200:
                            with open(tmp_file_path, 'wb') as out_file:
                                async for chunk in response.aiter_bytes(): out_file.write(chunk)
                            zipf.write(tmp_file_path, f["archive_path"])
                            os.remove(tmp_file_path)
                except Exception:
                    pass

    os.rmdir(temp_dir)
    return temp_zip.name, db_dir.name

async def rename_directory(directory_uid: uuid.UUID, new_name: str, session: AsyncSession, user: UserModel) -> DirectorySchema:
    db_dir = await check_directory_permission(directory_uid, session, user)
    db_dir.name = new_name
    await session.commit()
    await session.refresh(db_dir)
    return db_dir
