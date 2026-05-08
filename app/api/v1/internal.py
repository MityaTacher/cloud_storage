from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_session
from app.models import StorageNodeModel, FileModel

router = APIRouter(
    prefix='/v1/internal',
    tags=['Internal']
)

@router.post('/heartbeat')
async def node_heartbeat(
    name: str = Body(...),
    address: str = Body(...),
    internal_address: str = Body(...),
    total_space: int = Body(...),
    free_space: int = Body(...),
    rx_bytes: int = Body(0),
    tx_bytes: int = Body(0),
    cpu_percent: float = Body(0.0),
    ram_percent: float = Body(0.0),
    db: AsyncSession = Depends(get_async_session)
):
    node = (await db.scalars(select(StorageNodeModel).where(StorageNodeModel.name == name))).first()
    if not node:
        node = StorageNodeModel(
            name=name, address=address, internal_address=internal_address, 
            total_space_bytes=total_space, free_space_bytes=free_space,
            rx_bytes_per_sec=rx_bytes, tx_bytes_per_sec=tx_bytes,
            cpu_percent=cpu_percent, ram_percent=ram_percent
        )
        db.add(node)
    else:
        node.address = address
        node.internal_address = internal_address
        node.total_space_bytes = total_space
        node.free_space_bytes = free_space
        node.rx_bytes_per_sec = rx_bytes
        node.tx_bytes_per_sec = tx_bytes
        node.cpu_percent = cpu_percent
        node.ram_percent = ram_percent
    await db.commit()
    return {"status": "ok"}

@router.post('/webhook/upload-success')
async def upload_success(
    file_id: int = Body(...),
    storage_path: str = Body(...),
    actual_size: int = Body(...),
    db: AsyncSession = Depends(get_async_session)
):
    file = (await db.scalars(select(FileModel).where(FileModel.id == file_id))).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.status = "READY"
    file.path = storage_path
    file.size_bytes = actual_size
    await db.commit()
    return {"status": "ok"}

@router.post('/gc-check')
async def gc_check(
    node_name: str = Body(...),
    files_on_disk: list[str] = Body(...),
    db: AsyncSession = Depends(get_async_session)
):
    node = (await db.scalars(select(StorageNodeModel).where(StorageNodeModel.name == node_name))).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    db_files = (await db.scalars(select(FileModel.path).where(FileModel.node_id == node.id))).all()
    db_files_set = set(db_files)
    to_delete = [f for f in files_on_disk if f not in db_files_set]
    return {"delete": to_delete}
