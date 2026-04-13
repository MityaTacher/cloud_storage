from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    database_url: str = Field(
        default='postgresql+asyncpg://postgres:postgres@db:5432/postgres_typo',
        validation_alias='DATABASE_URL'
    )
    log_level: str = 'INFO'

    upload_dir: str = 'upload/'

    algorithm: str = 'SH256'
    secret_key: str = '32 symbols'

    access_token_expires_minutes: int = 15
    refresh_token_expires_days: int = 30

settings = Settings()
