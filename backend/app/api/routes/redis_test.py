from fastapi import APIRouter
from app.schemas.common import APIError, APIResponse

router = APIRouter(prefix="/redis-test")


@router.get("/ping", response_model=APIResponse)
def redis_ping() -> APIResponse:
    return APIResponse(success=False, error=APIError(code="NOT_CONFIGURED", message="Redis not configured"))


@router.get("/info", response_model=APIResponse)
def redis_info() -> APIResponse:
    return APIResponse(success=False, error=APIError(code="NOT_CONFIGURED", message="Redis not configured"))


@router.post("/read-write", response_model=APIResponse)
def redis_read_write() -> APIResponse:
    return APIResponse(success=False, error=APIError(code="NOT_CONFIGURED", message="Redis not configured"))
