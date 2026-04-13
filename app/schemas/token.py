from pydantic import BaseModel
from datetime import datetime


class RefreshTokenRequest(BaseModel):
    token: str


class TokenPayload(BaseModel):
    sub: str
    iat: datetime
    exp: datetime
    jti: str | None = None
    role: str | None = None
    token_type: str