from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from datetime import datetime, timedelta, UTC
from sqlalchemy import delete

from app.api.v1.router import router
from app.db.session import async_session_maker
from app.models import FileModel

app = FastAPI(description='Cloud storage', version='0.1')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

async def master_gc():
    while True:
        try:
            async with async_session_maker() as session:
                time_threshold = datetime.now(UTC) - timedelta(hours=1)
                await session.execute(
                    delete(FileModel).where(
                        FileModel.status == "PENDING", 
                        FileModel.loaded_at < time_threshold
                    )
                )
                await session.commit()
        except Exception as e:
            print(f"Master GC Error: {e}")
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(master_gc())

@app.get('/', status_code=status.HTTP_200_OK)
def home_page():
    return {'message': 'Hello FastAPI'}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)