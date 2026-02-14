# Nexus AI Hackathon Backend

## Local dev

Backend:
- `cd backend`
- `python -m venv .venv`
- `./.venv/Scripts/activate`
- `pip install -r requirements.txt`
- `uvicorn app.main:app --reload`

Frontend:
- `cd frontend`
- `npm install`
- `npm run dev`

Default API base: `http://localhost:8000`

## Ingestion Demo (CSV Auto-Pickup)

1. Start backend with the scheduler enabled (default):
   - `cd backend`
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Seed a demo data center + CSV connector:
   - `python scripts/seed_ingestion_demo.py`
3. The demo CSVs live in `backend/data/ingest/demo/`.
   - Scheduler picks them up automatically and moves to `processed/`.
4. Verify:
   - `GET /api/v1/data-centers`
   - `GET /api/v1/ingest/status`

## Ingestion Demo (DB Connector)

1. Start backend:
   - `cd backend`
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Seed a demo source database + connector:
   - `python scripts/seed_db_connector_demo.py`
3. Trigger a sync (or wait for scheduler):
   - `POST /api/v1/ingest/sync` with `{"data_center_id": <id>}`
4. Verify:
   - `GET /api/v1/data-centers`
   - `GET /api/v1/ingest/status`
