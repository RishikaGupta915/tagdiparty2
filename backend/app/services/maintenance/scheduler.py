import asyncio
import logging
from typing import Optional
from app.core.config import get_settings
from app.db.session import SessionLocalPrimary
from app.services.maintenance.archive import refresh_daily_transaction_metrics

logger = logging.getLogger(__name__)

_task: Optional[asyncio.Task] = None


async def _run_scheduler(interval_minutes: int) -> None:
    while True:
        try:
            with SessionLocalPrimary() as session:
                refresh_daily_transaction_metrics(session)
            logger.info("maintenance.refresh_daily_transaction_metrics completed")
        except Exception as exc:
            logger.exception("maintenance scheduler error: %s", exc)
        await asyncio.sleep(interval_minutes * 60)


def start_scheduler() -> None:
    global _task
    settings = get_settings()
    if not settings.maintenance_enabled:
        return
    if _task is None or _task.done():
        _task = asyncio.create_task(_run_scheduler(settings.maintenance_interval_minutes))


def stop_scheduler() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
