import hashlib
import jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/token")

def hash_password(password: str) -> str:
    """
    Медленное хэширование для пароля через чистый bcrypt
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def hash_token(token: str) -> str:
    """
    Быстрое хэширование для refresh-токена
    """
    return hashlib.sha256(token.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    pwd_bytes = password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

def verify_token(token: str, hashed_token: str) -> bool:
    return hash_token(token) == hashed_token

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode.update({'token_type': 'access'})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    to_encode.update({'token_type': 'refresh'})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str, expected_type: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        token_data = TokenPayload(**payload)

        if token_data.token_type != expected_type:
            raise jwt.PyJWTError("Invalid token type")

        return token_data

    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
