from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import jwt
import asyncio
import shutil
import psutil
import time

app = FastAPI(title="Storage Node")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MASTER_URL = os.getenv("MASTER_URL", "http://master:8000")
NODE_NAME = os.getenv("NODE_NAME", "storage-1")
NODE_ADDRESS = os.getenv("NODE_ADDRESS", "http://localhost:8001")
NODE_INTERNAL_ADDRESS = os.getenv("NODE_INTERNAL_ADDRESS", "http://storage-1:8001")
CLUSTER_SECRET = os.getenv("CLUSTER_SECRET", "super-secret-key-for-internal-auth")
STORAGE_DIR = os.getenv("STORAGE_DIR", "/data")

os.makedirs(STORAGE_DIR, exist_ok=True)

async def heartbeat():
    last_net = psutil.net_io_counters()
    last_time = time.time()
    
    psutil.cpu_percent(interval=None)
    
    while True:
        try:
            stat = os.statvfs(STORAGE_DIR)
            free_space = stat.f_bavail * stat.f_frsize
            total_space = stat.f_blocks * stat.f_frsize
            
            current_net = psutil.net_io_counters()
            current_time = time.time()
            time_diff = current_time - last_time
            rx_bytes_sec = (current_net.bytes_recv - last_net.bytes_recv) / time_diff if time_diff > 0 else 0
            tx_bytes_sec = (current_net.bytes_sent - last_net.bytes_sent) / time_diff if time_diff > 0 else 0
            
            last_net = current_net
            last_time = current_time

            cpu_usage = psutil.cpu_percent(interval=None)
            ram_usage = psutil.virtual_memory().percent

            async with httpx.AsyncClient() as client:
                await client.post(f"{MASTER_URL}/api/v1/internal/heartbeat", json={
                    "name": NODE_NAME, 
                    "address": NODE_ADDRESS,
                    "internal_address": NODE_INTERNAL_ADDRESS,
                    "total_space": total_space, 
                    "free_space": free_space,
                    "rx_bytes": int(rx_bytes_sec),
                    "tx_bytes": int(tx_bytes_sec),
                    "cpu_percent": cpu_usage,
                    "ram_percent": ram_usage
                })
        except Exception as e:
            print(f"Heartbeat error: {e}")
        await asyncio.sleep(15)

async def garbage_collector():
    while True:
        await asyncio.sleep(3600)
        try:
            files_on_disk = os.listdir(STORAGE_DIR)
            async with httpx.AsyncClient() as client:
                res = await client.post(f"{MASTER_URL}/api/v1/internal/gc-check", json={"node_name": NODE_NAME, "files_on_disk": files_on_disk})
                to_delete = res.json().get("delete", [])
                for f in to_delete:
                    try:
                        os.remove(os.path.join(STORAGE_DIR, f))
                    except FileNotFoundError:
                        pass
        except Exception as e:
            print(f"GC error: {e}")

@app.on_event("startup")
async def startup():
    asyncio.create_task(heartbeat())
    asyncio.create_task(garbage_collector())

def decode_token(token: str, action: str):
    try:
        payload = jwt.decode(token, CLUSTER_SECRET, algorithms=["HS256"])
        if payload.get("action") != action: raise HTTPException(403)
        return payload
    except Exception:
        raise HTTPException(403, "Invalid token")

@app.post("/api/storage/upload")
async def upload_file(token: str, file: UploadFile = File(...)):
    payload = decode_token(token, "upload")
    filepath = os.path.join(STORAGE_DIR, payload["path"])
    
    with open(filepath, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)
            
    async with httpx.AsyncClient() as client:
        await client.post(f"{MASTER_URL}/api/v1/internal/webhook/upload-success", json={
            "file_id": payload["file_id"], "storage_path": payload["path"], "actual_size": os.path.getsize(filepath)
        })
    return {"status": "ok"}

@app.get("/api/storage/download")
async def download_file(token: str):
    payload = decode_token(token, "download")
    filepath = os.path.join(STORAGE_DIR, payload["path"])
    return FileResponse(path=filepath, filename=payload["filename"])

@app.get("/api/storage/internal/download")
async def internal_download(token: str):
    payload = decode_token(token, "internal_download")
    filepath = os.path.join(STORAGE_DIR, payload["path"])
    return FileResponse(path=filepath)

@app.post("/api/storage/internal/copy")
async def internal_copy(token: str):
    payload = decode_token(token, "copy")
    src = os.path.join(STORAGE_DIR, payload["src_path"])
    dest = os.path.join(STORAGE_DIR, payload["dest_path"])
    try:
        shutil.copy2(src, dest)
        return {"status": "ok"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Source not found")

@app.delete("/api/storage/delete")
async def delete_file(token: str):
    payload = decode_token(token, "delete")
    try:
        os.remove(os.path.join(STORAGE_DIR, payload["path"]))
    except FileNotFoundError:
        pass
    return {"status": "ok"}
