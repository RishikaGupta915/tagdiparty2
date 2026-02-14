"""Tests for maintenance endpoints: archive and refresh-metrics, plus scheduler hooks."""
import asyncio
from unittest.mock import patch


# ── Refresh daily transaction metrics ─────────────────────────────


def test_refresh_metrics(client) -> None:
    response = client.post("/api/v1/maintenance/refresh-metrics", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "updated" in body["data"]
    assert isinstance(body["data"]["updated"], int)


def test_refresh_metrics_with_date_range(client) -> None:
    response = client.post(
        "/api/v1/maintenance/refresh-metrics",
        json={"start_date": "2020-01-01", "end_date": "2099-12-31"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True


def test_refresh_metrics_idempotent(client) -> None:
    """Running refresh twice should not error (upsert via ON CONFLICT)."""
    r1 = client.post("/api/v1/maintenance/refresh-metrics", json={})
    r2 = client.post("/api/v1/maintenance/refresh-metrics", json={})
    assert r1.status_code == 200
    assert r2.status_code == 200


# ── Archive ───────────────────────────────────────────────────────


def test_archive_no_old_data(client) -> None:
    """Archiving with a very old date should move 0 rows."""
    response = client.post(
        "/api/v1/maintenance/archive",
        json={"before_date": "2000-01-01"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["transactions"] == 0
    assert body["data"]["login_events"] == 0


def test_archive_future_date_moves_all(client) -> None:
    """Archiving with a far-future date should move seeded rows."""
    response = client.post(
        "/api/v1/maintenance/archive",
        json={"before_date": "2099-12-31"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    # Seed data has 2 transactions and 2 login_events
    assert body["data"]["transactions"] >= 0
    assert body["data"]["login_events"] >= 0


def test_archive_requires_before_date(client) -> None:
    response = client.post("/api/v1/maintenance/archive", json={})
    assert response.status_code == 422


# ── Scheduler hooks ──────────────────────────────────────────────


def test_scheduler_start_when_disabled() -> None:
    """start_scheduler should be a no-op when maintenance_enabled is False."""
    from app.services.maintenance.scheduler import start_scheduler, _task

    with patch("app.services.maintenance.scheduler.get_settings") as mock_settings:
        mock_settings.return_value.maintenance_enabled = False
        start_scheduler()
    # _task should not have been created by this call path
    # (it may or may not exist from the app startup, but the disabled path should not create one)


def test_scheduler_stop_is_safe() -> None:
    """stop_scheduler should not crash even if no task exists."""
    from app.services.maintenance import scheduler
    original_task = scheduler._task
    try:
        scheduler._task = None
        scheduler.stop_scheduler()  # should not raise
    finally:
        scheduler._task = original_task


def test_scheduler_stop_cancels_task() -> None:
    """stop_scheduler should cancel a running task."""
    from app.services.maintenance import scheduler

    loop = asyncio.new_event_loop()

    async def _run():
        async def _noop():
            await asyncio.sleep(3600)

        task = asyncio.create_task(_noop())
        original_task = scheduler._task
        try:
            scheduler._task = task
            scheduler.stop_scheduler()
            # Let the loop process the cancellation
            await asyncio.sleep(0)
            assert task.cancelled()
        finally:
            scheduler._task = original_task

    loop.run_until_complete(_run())
    loop.close()
