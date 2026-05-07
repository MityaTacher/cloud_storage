from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.v1.router import router

app = FastAPI(description='Cloud storage', version='0.1', summary='...')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get('/', status_code=status.HTTP_200_OK)
def home_page():
    return {'message': 'Hello FastAPI'}

if __name__ == "__main__":
    uvicorn.run(app, port=1212)