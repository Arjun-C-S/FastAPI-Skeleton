from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str
    APP_ENV: str
    APP_PORT: int

    # Postgres
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Redis
    REDIS_URL: str
    CACHE_TTL: int

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:8000"]

    class Config:
        env_file = ".env"


settings = Settings()
