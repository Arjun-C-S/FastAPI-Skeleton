from pydantic import BaseModel


class ApiResponse[T](BaseModel):
    success: bool
    message: str
    data: T | None = None
    errors: list[str] | None = None
