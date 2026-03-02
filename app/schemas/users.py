from pydantic import ConfigDict, BaseModel, Field, EmailStr, SecretStr
from datetime import datetime


class UserBase(BaseModel):
    """
    Базовая модель, которая содержит поля, используемые во всех наследуемых моделях.
    """
    email: EmailStr = Field(description='Email пользователя')
    username: str = Field(description='Уникальный никнейм пользователя')

class UserCreate(UserBase):
    """
    Модель для создания пользователя.
    Используется в POST запросах.
    """
    password: SecretStr = Field(min_length=4, description='Пароль пользователя')
    # role: str = Field(default='user', description='Роль пользователя: user/admin')

class UserUpdate(UserBase):
    """
    ...
    """
    role: str | None = Field(default=None, description='Роль пользователя: user/admin')

class User(UserBase):
    """
    Модель для ответа с данными о пользователе.
    Используется в GET запросах.
    """
    id: int = Field(description='id пользователя')
    registered_at: datetime = Field(description='Дата и время регистрации пользователя')
    role: str = Field(description='Роль пользователя: user/admin')
    model_config = ConfigDict(from_attributes=True)


