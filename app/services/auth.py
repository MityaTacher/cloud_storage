from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

import hashlib

import jwt
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.token import TokenPayload


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


def hash_password(password: str) -> str:
    """
    Медленное хэширование для пароля
    """
    return pwd_context.hash(password)


def hash_token(token: str) -> str:
    """
    Быстрое хэширования для refresh-токена
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def verify_token(token: str, hashed_token:str) -> bool:
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
