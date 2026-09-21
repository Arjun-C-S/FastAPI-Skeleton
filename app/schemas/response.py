from pydantic import BaseModel


class HealthData(BaseModel):
    env: str


class ApiResponse[T](BaseModel):
    success: bool
    message: str
    data: T | None = None
    errors: list[str] | None = None
