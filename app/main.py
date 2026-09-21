from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.db.redis import connect_redis, disconnect_redis
from app.middleware.logging import RequestLoggingMiddleware, configure_logging
from app.schemas.response import ApiResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    configure_logging(settings.APP_ENV)
    await connect_redis()
    yield
    await disconnect_redis()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)


register_exception_handlers(app)


@app.get("/health", response_model=ApiResponse)
async def health() -> ApiResponse:
    return ApiResponse[dict[str, str]](
        success=True,
        message="Server is running",
        data={"env": settings.APP_ENV},
    )
