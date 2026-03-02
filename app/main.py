from fastapi import FastAPI, status
import uvicorn

app = FastAPI(description='Claude storage', version='0.1', summary='...')


@app.get('/', status_code=status.HTTP_200_OK)
def home_page():
    return {'message': 'Hello FastAPI'}

if __name__ == "__main__":
    uvicorn.run(app, port=1212)