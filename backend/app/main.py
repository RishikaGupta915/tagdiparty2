from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.services.maintenance.scheduler import start_scheduler, stop_scheduler
from app.services.ingestion.scheduler import start_ingestion_scheduler, stop_ingestion_scheduler

settings = get_settings()

configure_logging()

app = FastAPI(title=settings.app_name)

cors_origins = settings.cors_origin_list
allow_credentials = True
if "*" in cors_origins:
    cors_origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    init_db(settings.database_url)
    start_scheduler()
    start_ingestion_scheduler()


@app.on_event("shutdown")
def shutdown() -> None:
    stop_scheduler()
    stop_ingestion_scheduler()
