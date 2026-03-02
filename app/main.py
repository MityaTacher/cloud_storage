from fastapi import FastAPI, status
import uvicorn

from app.api.v1.router import router

app = FastAPI(description='Cloud storage', version='0.1', summary='...')

app.include_router(router)

@app.get('/', status_code=status.HTTP_200_OK)
def home_page():
    return {'message': 'Hello FastAPI'}

if __name__ == "__main__":
    uvicorn.run(app, port=1212)