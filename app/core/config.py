from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str
    APP_ENV: str
    APP_PORT: int

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    REDIS_URL: str
    CACHE_TTL: int

    ALLOWED_ORIGINS: list[str] = ["http://localhost:8000"]


settings = Settings()
