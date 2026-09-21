from http import HTTPStatus


class AppException(Exception):
    def __init__(self, status_code: int, message: str, errors: list[str] | None = None):
        self.status_code = status_code
        self.message = message
        self.errors = errors


class NotFoundException(AppException):
    def __init__(self, message: str = "Not found"):
        super().__init__(HTTPStatus.NOT_FOUND.value, message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(HTTPStatus.UNAUTHORIZED.value, message)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(HTTPStatus.BAD_REQUEST.value, message)
