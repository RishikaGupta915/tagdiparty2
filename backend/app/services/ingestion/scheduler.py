import asyncio
import logging
from typing import Optional
from sqlalchemy import select
from app.core.config import get_settings
from app.db.session import SessionLocalPrimary
from app.models.ingestion import DataCenterSource
from app.services.ingestion.sync import sync_source

logger = logging.getLogger(__name__)

_task: Optional[asyncio.Task] = None


async def _run_scheduler(interval_minutes: int) -> None:
    while True:
        try:
            with SessionLocalPrimary() as session:
                sources = list(session.execute(select(DataCenterSource)).scalars())
                for source in sources:
                    if source.status == "disabled":
                        continue
                    sync_source(session, source)
            logger.info("ingestion scheduler run completed")
        except Exception as exc:
            logger.exception("ingestion scheduler error: %s", exc)
        await asyncio.sleep(interval_minutes * 60)


def start_ingestion_scheduler() -> None:
    global _task
    settings = get_settings()
    if not settings.ingestion_enabled:
        return
    if _task is None or _task.done():
        _task = asyncio.create_task(_run_scheduler(settings.ingestion_interval_minutes))


def stop_ingestion_scheduler() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
