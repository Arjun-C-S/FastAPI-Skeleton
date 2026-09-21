import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


def configure_logging(env: str) -> None:
    level = logging.DEBUG if env == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        force=True,
    )


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s status=%s duration=%.2fms request_id=%s",
                request.method,
                request.url.path,
                500,
                duration,
                request_id,
            )
            raise

        duration = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s status=%s duration=%.2fms request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            request_id,
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
