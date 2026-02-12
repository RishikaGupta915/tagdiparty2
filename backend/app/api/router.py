from fastapi import APIRouter
from app.api.routes import health, query, alert, alerts, sentinel, dashboards, db_test, redis_test

router = APIRouter()

router.include_router(health.router)
router.include_router(query.router)
router.include_router(alert.router)
router.include_router(alerts.router)
router.include_router(sentinel.router)
router.include_router(dashboards.router)
router.include_router(db_test.router)
router.include_router(redis_test.router)
