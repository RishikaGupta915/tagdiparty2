from fastapi import APIRouter
from app.schemas.common import APIResponse
from app.core.config import get_settings

router = APIRouter()


@router.get("/health", response_model=APIResponse)
def health() -> APIResponse:
    settings = get_settings()
    return APIResponse(success=True, data={"status": "ok", "env": settings.env})
