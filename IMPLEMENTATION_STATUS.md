# Implementation Status Report

**Project:** Multi-Data-Center Collection & Analytics Platform (Nexus AI)  
**Date:** 2026-02-13  
**Assessed Against:** [PRD.md](PRD.md)

---

## Overview

| Area                        | Status                                                |
| --------------------------- | ----------------------------------------------------- |
| NL2SQL Engine               | **Complete**                                          |
| Sentinel Agent              | **Complete**                                          |
| Alerts & Monitoring         | **Partial** — CRUD done, evaluation/detection missing |
| Dashboards                  | **Partial** — backend CRUD exists, no frontend UI     |
| Data Collection & Ingestion | **Not Started**                                       |
| Frontend UI                 | **Partial** — 2 of 6+ required pages built            |
| Deployment (Docker)         | **Complete**                                          |
| CI/CD                       | **Not Started**                                       |

---

## IMPLEMENTED

### Backend API Routes

| Endpoint                              | Method | Description                        | File                                    |
| ------------------------------------- | ------ | ---------------------------------- | --------------------------------------- |
| `/health`                             | GET    | Health check                       | `backend/app/api/routes/health.py`      |
| `/api/v1/query`                       | POST   | NL2SQL query pipeline              | `backend/app/api/routes/query.py`       |
| `/api/v1/alert`                       | POST   | Ingest a single alert event        | `backend/app/api/routes/alert.py`       |
| `/api/v1/alerts/metrics`              | GET    | List all alert metrics             | `backend/app/api/routes/alerts.py`      |
| `/api/v1/alerts/metrics`              | POST   | Create alert metric                | `backend/app/api/routes/alerts.py`      |
| `/api/v1/alerts/metrics/{id}`         | PUT    | Update alert metric                | `backend/app/api/routes/alerts.py`      |
| `/api/v1/alerts/metrics/{id}`         | DELETE | Delete alert metric                | `backend/app/api/routes/alerts.py`      |
| `/api/v1/alerts/history`              | GET    | List alert history                 | `backend/app/api/routes/alerts.py`      |
| `/api/v1/alerts/anomalies`            | GET    | List anomaly history               | `backend/app/api/routes/alerts.py`      |
| `/api/v1/sentinel/scan`               | GET    | Run sentinel scan (sync)           | `backend/app/api/routes/sentinel.py`    |
| `/api/v1/sentinel/scan/stream`        | GET    | Run sentinel scan (SSE stream)     | `backend/app/api/routes/sentinel.py`    |
| `/api/v1/sentinel/history`            | GET    | List scan history                  | `backend/app/api/routes/sentinel.py`    |
| `/api/v1/sentinel/history/{scan_id}`  | GET    | Get scan detail                    | `backend/app/api/routes/sentinel.py`    |
| `/api/v1/dashboards`                  | GET    | List dashboards                    | `backend/app/api/routes/dashboards.py`  |
| `/api/v1/dashboards`                  | POST   | Create dashboard                   | `backend/app/api/routes/dashboards.py`  |
| `/api/v1/dashboards/{id}`             | GET    | Get dashboard by ID                | `backend/app/api/routes/dashboards.py`  |
| `/api/v1/maintenance/refresh-metrics` | POST   | Refresh daily transaction metrics  | `backend/app/api/routes/maintenance.py` |
| `/api/v1/maintenance/archive`         | POST   | Archive old data                   | `backend/app/api/routes/maintenance.py` |
| `/api/db-test/health`                 | GET    | DB connectivity check              | `backend/app/api/routes/db_test.py`     |
| `/api/db-test/tables`                 | GET    | List DB tables                     | `backend/app/api/routes/db_test.py`     |
| `/api/db-test/schema`                 | GET    | Primary DB schema introspection    | `backend/app/api/routes/db_test.py`     |
| `/api/db-test/alerts`                 | GET    | Alerts DB schema introspection     | `backend/app/api/routes/db_test.py`     |
| `/api/db-test/dashboards`             | GET    | Dashboards DB schema introspection | `backend/app/api/routes/db_test.py`     |

### NL2SQL Engine (Complete)

| Component               | File                                       | Description                                                                 |
| ----------------------- | ------------------------------------------ | --------------------------------------------------------------------------- |
| Pipeline orchestrator   | `backend/app/services/nl2sql/engine.py`    | `run_query_pipeline()` — runs graph, executes SQL, generates viz + insights |
| LangGraph state machine | `backend/app/services/nl2sql/graph.py`     | `load_schema → route → generate_sql → validate → END`                       |
| LLM integration         | `backend/app/services/nl2sql/llm.py`       | Supports OpenAI + Gemini via LangChain                                      |
| Domain prompts          | `backend/app/services/nl2sql/prompts.py`   | 5 domains: security, compliance, risk, operations, general                  |
| Rule-based generator    | `backend/app/services/nl2sql/rules.py`     | Intent/table detection, date filters, grouping, limits                      |
| SQL validator           | `backend/app/services/nl2sql/validator.py` | Read-only enforcement via sqlglot                                           |
| SQL repair              | `backend/app/services/nl2sql/repair.py`    | Auto-adds LIMIT 100                                                         |
| Schema introspection    | `backend/app/services/nl2sql/schema.py`    | Builds `{table: [columns]}` from live DB                                    |

### Sentinel Agent (Complete)

| Component   | File                                      | Description                                                                                                                       |
| ----------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Scan engine | `backend/app/services/sentinel/engine.py` | Domain-based missions, risk scoring, deep-dives, cross-correlation, narrative generation, scan history persistence, SSE streaming |

### Data Model (Partial)

**Primary DB (`derivinsightnew.db`):**

| Model                    | Table                       | Status                                                                |
| ------------------------ | --------------------------- | --------------------------------------------------------------------- |
| `User`                   | `users`                     | Done — `id, name, email, role, created_at`                            |
| `Transaction`            | `transactions`              | Done — `id, user_id, amount, currency, status, created_at`            |
| `LoginEvent`             | `login_events`              | Done — `id, user_id, ip_address, success, created_at, metadata`       |
| `TransactionArchive`     | `transactions_archive`      | Done                                                                  |
| `LoginEventArchive`      | `login_events_archive`      | Done                                                                  |
| `DailyTransactionMetric` | `daily_transaction_metrics` | Done                                                                  |
| `ScanHistory`            | `scan_history`              | Done — `scan_id, domain, status, risk_score, result_json, created_at` |

**Alerts DB (`derivinsight_alerts.db`):**

| Model            | Table             | Status                               |
| ---------------- | ----------------- | ------------------------------------ |
| `Metric`         | `metrics`         | Done                                 |
| `Event`          | `events`          | Done                                 |
| `AlertHistory`   | `alert_history`   | Done (table exists, never populated) |
| `AnomalyHistory` | `anomaly_history` | Done (table exists, never populated) |

**Dashboards DB (`deriveinsights_dashboard.db`):**

| Model       | Table        | Status                                                  |
| ----------- | ------------ | ------------------------------------------------------- |
| `Dashboard` | `dashboards` | Done — `id, name, description, config_json, created_at` |

### Maintenance Services (Complete)

| Component            | File                                            | Description                                                       |
| -------------------- | ----------------------------------------------- | ----------------------------------------------------------------- |
| Archive service      | `backend/app/services/maintenance/archive.py`   | Archives old transactions + login events, refreshes daily metrics |
| Background scheduler | `backend/app/services/maintenance/scheduler.py` | Runs metric refresh every 15 min via asyncio                      |

### Configuration & Infrastructure (Complete)

| Component      | File                          | Description                                                         |
| -------------- | ----------------------------- | ------------------------------------------------------------------- |
| Settings       | `backend/app/core/config.py`  | pydantic-settings with all env vars (DB URLs, CORS, LLM keys, etc.) |
| DB sessions    | `backend/app/db/session.py`   | 3 SQLAlchemy engines, SQLite pragmas, dependency generators         |
| DB init + seed | `backend/app/db/init_db.py`   | Table creation, demo seed data (2 users, 2 tx, 2 logins)            |
| Logging        | `backend/app/core/logging.py` | Basic `INFO` level logging                                          |
| App bootstrap  | `backend/app/main.py`         | FastAPI app, CORS, router, startup/shutdown hooks                   |

### Deployment (Partial)

| Component           | File                         | Status                                      |
| ------------------- | ---------------------------- | ------------------------------------------- |
| Backend Dockerfile  | `docker/backend.Dockerfile`  | Done — Python 3.11-slim, uvicorn            |
| Frontend Dockerfile | `docker/frontend.Dockerfile` | Done — Node 20 build → nginx serve          |
| Docker Compose      | `docker-compose.yml`         | Done — 2 services, SQLite volumes, env vars |

### Frontend (Partial)

| Feature                 | Status                                                                  |
| ----------------------- | ----------------------------------------------------------------------- |
| NL2SQL chat interface   | Done — text input, chat bubbles, SQL display, data table, CSV export    |
| Sentinel dashboard      | Done — SSE streaming, risk gauge, findings table, narrative, CSV export |
| Domain selector         | Done — general, security, compliance, risk, operations                  |
| Health status indicator | Done — green/orange dot                                                 |
| Dark theme UI           | Done — glassmorphism, `Sora` font, responsive at 720px                  |

### Tests (~75 total)

| Test File                 | Coverage                                                | Count |
| ------------------------- | ------------------------------------------------------- | ----- |
| `test_health.py`          | Health endpoint                                         | 1     |
| `test_db.py`              | DB connectivity, tables, schema, seed data              | 6     |
| `test_query.py`           | NL2SQL query                                            | 1     |
| `test_alerts.py`          | Event ingestion, metrics CRUD, history, anomalies       | 10    |
| `test_sentinel.py`        | All domains, history, SSE stream                        | 10    |
| `test_maintenance.py`     | Refresh, archive, scheduler                             | 8     |
| `test_llm_integration.py` | Prompts, parsing, LLM client, graph, validation, repair | ~39   |

---

## NOT IMPLEMENTED

### 1. Data Collection & Ingestion Pipeline (PRD Milestone #1 — Not Started)

**Missing API Endpoints:**

| Endpoint                | Method | PRD Requirement                |
| ----------------------- | ------ | ------------------------------ |
| `/api/v1/ingest/upload` | POST   | CSV file ingestion             |
| `/api/v1/ingest/sync`   | POST   | Trigger sync for a data center |
| `/api/v1/ingest/status` | GET    | Latest ingestion status        |
| `/api/v1/data-centers`  | GET    | List data sources + health     |

**Missing Backend Services:**

- Configurable connectors per data center (SQLAlchemy URL, CSV, API)
- Scheduled ingestion with automatic polling (no manual trigger)
- Incremental sync support
- Schema normalization and mapping into canonical tables
- Automated CSV file pickup
- Data freshness tracking per source
- Ingestion failure logging surfaced in UI

### 2. Data Model Gaps (PRD Milestone #2 — Partial)

**Missing fields on existing tables:**

| Field            | Requirement                   |
| ---------------- | ----------------------------- |
| `source_id`      | Must be on all canonical rows |
| `data_center_id` | Must be on all canonical rows |
| `ingested_at`    | Must be on all canonical rows |

**Missing metadata tables:**

| Table             | Fields                                            | Purpose                      |
| ----------------- | ------------------------------------------------- | ---------------------------- |
| `data_centers`    | `id, name, status, last_sync`                     | Track connected data centers |
| `ingestion_runs`  | `id, source_id, status, records_ingested, errors` | Track each ingestion job     |
| `schema_registry` | `table, version, columns`                         | Schema versioning            |

### 3. Alert Metric Evaluation & Anomaly Detection (PRD Milestone #4 — Stub)

| Requirement                     | Current State                        |
| ------------------------------- | ------------------------------------ |
| `evaluate_metrics()` function   | Stub — returns `None`, never invoked |
| Sliding window evaluation       | Not built                            |
| Anomaly / spike detection       | Not built                            |
| `alert_history` population      | Table exists but never written to    |
| `anomaly_history` population    | Table exists but never written to    |
| Automated alerting on DC issues | Not built                            |

### 4. Dashboard CRUD Gaps

| Endpoint                  | Method | Status    |
| ------------------------- | ------ | --------- |
| `/api/v1/dashboards/{id}` | PUT    | Not built |
| `/api/v1/dashboards/{id}` | DELETE | Not built |

### 5. Frontend Pages & Features (PRD Capability #5 — Major Gaps)

| Required Page/Feature                              | Status                                          |
| -------------------------------------------------- | ----------------------------------------------- |
| Data center overview dashboard                     | Not built                                       |
| Alerts management page (rules, history, triggered) | Not built — backend API exists                  |
| Saved dashboards page (CRUD)                       | Not built — backend API exists                  |
| Maintenance / archive page                         | Not built — backend API exists                  |
| Ingestion status / streaming indicator             | Not built                                       |
| Line charts, pie charts                            | Not built — only bar + metric card              |
| React Router / URL navigation                      | Not built — single-file tab switching           |
| Component splitting                                | Not built — entire UI in one 422-line `App.jsx` |
| Loading states / skeletons                         | Not built — only boolean flags                  |
| Pagination                                         | Not built                                       |
| Frontend tests                                     | None                                            |
| Real charting library (Recharts, D3, etc.)         | Not installed — hand-rolled CSS/SVG only        |

### 6. Redis Integration

| Requirement                       | Current State                   |
| --------------------------------- | ------------------------------- |
| Redis client                      | Not configured                  |
| Redis in Docker Compose           | Not defined                     |
| `/redis-test/*` endpoints         | Return `"NOT_CONFIGURED"` stubs |
| Sliding window caching for alerts | Not built                       |

### 7. CI/CD (PRD Milestone #6 — Not Started)

| Requirement             | Status    |
| ----------------------- | --------- |
| GitHub Actions workflow | Not built |
| CI for tests + build    | Not built |
| Deployment validation   | Not built |

### 8. Operational Quality Gaps

| Requirement                          | Current State                                                     |
| ------------------------------------ | ----------------------------------------------------------------- |
| Structured logging / request tracing | Minimal — `basicConfig(INFO)` only                                |
| Global exception handler             | Not built — relies on FastAPI defaults                            |
| Consistent API error responses       | Partial — `APIResponse` schema exists but not enforced everywhere |
| Pydantic response models on routes   | Defined but unused — routes return raw dicts                      |

---

## Priority Roadmap

| Priority | Milestone                                                  | Effort | Status      |
| -------- | ---------------------------------------------------------- | ------ | ----------- |
| **P0**   | Data source config + ingestion pipeline                    | Large  | Not Started |
| **P0**   | Data model updates (DC fields, metadata tables)            | Medium | Not Started |
| **P1**   | Alert evaluation engine + anomaly detection                | Medium | Stub exists |
| **P1**   | Frontend: data center overview + alerts + dashboards pages | Large  | Not Started |
| **P2**   | Dashboard update/delete endpoints                          | Small  | Not Started |
| **P2**   | Frontend: component splitting + React Router               | Medium | Not Started |
| **P2**   | Charting library integration                               | Medium | Not Started |
| **P3**   | Redis integration                                          | Medium | Stub exists |
| **P3**   | CI/CD (GitHub Actions)                                     | Medium | Not Started |
| **P3**   | Structured logging + global error handling                 | Small  | Not Started |
