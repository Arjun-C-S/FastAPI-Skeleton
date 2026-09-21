import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.middleware.logging import REQUEST_ID_HEADER, get_request_id
from app.schemas.response import ApiResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


def _json_error(
    request: Request,
    status_code: int,
    message: str,
    errors: list[str] | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content=ApiResponse(
            success=False,
            message=message,
            errors=errors,
        ).model_dump(),
    )
    request_id = get_request_id(request)
    if request_id:
        response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return _json_error(request, exc.status_code, exc.message, exc.errors)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _json_error(
        request,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "Validation error",
        [str(e) for e in exc.errors()],
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled error request_id=%s",
        get_request_id(request),
        exc_info=exc,
    )
    return _json_error(
        request,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "Internal server error",
    )
