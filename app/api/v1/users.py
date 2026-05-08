from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select, or_, Sequence, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas import UserSchema, UserCreate, FileSchema, RefreshTokenRequest, DirectoryRoot
from app.models import UserModel, StorageNodeModel, FileModel, DirectoryModel

from app.crud.user import (
    get_users,
    get_user_by_id,
    get_user_files,
    create_user,
    delete_user,
    login,
    refresh,
    get_current_user,
    get_current_admin,
    check_user_permissions,
    get_root
)



router = APIRouter(
    prefix='/v1/users',
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
    """
    ADMIN ONLY
    """
    return await get_users(db)


@router.get('/nodes/stats', status_code=status.HTTP_200_OK)
async def get_storage_nodes_endpoint(
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_admin),
):
    """
    ADMIN ONLY: Get storage nodes metrics
    """
    tmp = await db.scalars(select(StorageNodeModel))
    return tmp.all()


@router.get('/cloud', status_code=status.HTTP_200_OK)
async def get_root_endpoint(
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    return await get_root(db, user)


@router.get('/{user_id}', status_code=status.HTTP_200_OK, response_model=UserSchema)
async def get_user_endpoint(
        user_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    USER ONLY
    """
    await check_user_permissions(user_id, user, allow_admin=True)

    return await get_user_by_id(user_id, db)


@router.get('/{user_id}/files', status_code=status.HTTP_200_OK, response_model=list[FileSchema])
async def get_user_files_endpoint(
        user_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    USER ADMIN
    """
    await check_user_permissions(user_id, user, allow_admin=True)

    return await get_user_files(user_id, db)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def create_user_endpoint(
        user: UserCreate,
        db: AsyncSession = Depends(get_async_session)
):
    """
    ANY USER
    """
    return await create_user(user, db)


@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
        user_id: int,
        db: AsyncSession = Depends(get_async_session),
        user: UserModel = Depends(get_current_user)
):
    """
    USER ONLY
    """
    await check_user_permissions(user_id, user, allow_admin=True)
    await delete_user(user_id, db, user)

@router.get('/admin/dashboard', status_code=status.HTTP_200_OK)
async def get_admin_dashboard_stats(
    db: AsyncSession = Depends(get_async_session),
    user: UserModel = Depends(get_current_admin)
):
    total_files = await db.scalar(select(func.count(FileModel.id)))
    total_size = await db.scalar(select(func.sum(FileModel.size_bytes))) or 0
    
    pub_files = await db.scalar(select(func.count(FileModel.id)).where(FileModel.access_level == 1))
    pub_dirs = await db.scalar(select(func.count(DirectoryModel.uid)).where(DirectoryModel.access_level == 1))
    
    user_stats = await db.execute(
        select(UserModel, func.coalesce(func.sum(FileModel.size_bytes), 0))
        .outerjoin(FileModel, UserModel.id == FileModel.user_id)
        .group_by(UserModel.id)
    )
    users_data = []
    for u, used_bytes in user_stats.all():
        users_data.append({
            "id": u.id, "username": u.username, "email": u.email, 
            "role": u.role, "registered_at": u.registered_at, 
            "used_bytes": int(used_bytes)
        })

    all_files = (await db.execute(select(FileModel.filename, FileModel.size_bytes))).all()
    file_types = {"Images": 0, "Video": 0, "Documents": 0, "Archives": 0, "Audio": 0, "Others": 0}
    
    for fname, size in all_files:
        ext = fname.split('.')[-1].lower() if '.' in fname else ''
        sz = size or 0
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']: file_types["Images"] += sz
        elif ext in ['mp4', 'mov', 'avi', 'mkv']: file_types["Video"] += sz
        elif ext in ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pptx']: file_types["Documents"] += sz
        elif ext in ['zip', 'rar', '7z', 'tar', 'gz']: file_types["Archives"] += sz
        elif ext in ['mp3', 'wav', 'flac']: file_types["Audio"] += sz
        else: file_types["Others"] += sz

    return {
        "global": {
            "total_files": total_files,
            "total_size_bytes": int(total_size),
            "total_public_links": pub_files + pub_dirs
        },
        "file_types": file_types,
        "users": users_data
    }
