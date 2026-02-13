# PRD: Multi-Data-Center Collection & Analytics Platform
Date: 2026-02-13
Status: Updated requirements

## Summary
Build a centralized data collection and optimization platform that automatically pulls data from multiple data centers, consolidates it into a unified store, and powers dashboards, NL2SQL analytics, and proactive AI monitoring with alerting. The system must run continuously without manual intervention and provide real-time visibility across all connected data centers.

## Goals
- Automatically collect data from multiple data centers into a centralized store.
- Normalize and unify schemas so analytics can run across all sources.
- Provide dashboards, tables, and charts for quick analysis.
- Enable NL2SQL questions across the consolidated dataset.
- Run a proactive AI agent that continuously analyzes data and raises alerts.
- Support near-real-time monitoring with streaming updates.

## Non-Goals
- Full production security hardening (auth/RBAC, rate limiting) in this phase.
- Multi-tenant isolation.
- Arbitrary schema inference without configuration.

## Users
- Executive / Analyst: wants a unified view and high-level insights.
- Security / Compliance Lead: wants risk indicators and alerts.
- Ops Engineer: wants system health and data freshness monitoring.

## Tech Stack (Must Use)
- Backend: Python + FastAPI
- Orchestration: LangGraph + LangChain
- LLMs: Google Gemini (default), OpenAI (optional)
- Frontend: React
- Storage: SQLite by default (configurable to MySQL/Postgres)
- Deploy: Docker + GitHub Actions

## Data Sources & Collection (Must Implement)
- Support multiple data centers as sources.
- Each data center may expose:
  - Database connection (SQLAlchemy URL)
  - File drops (CSV) for batch ingestion
  - Optional API endpoints
- Automatic polling and ingestion with no manual trigger.
- Data freshness tracking per source.
- Ingestion failures must be logged and surfaced in UI.

## Data Model (Must Define)
### Centralized Store
- `users`, `transactions`, `login_events` (canonical datasets)
- Additional `source_id`, `data_center_id`, and `ingested_at` fields on all rows.
- Metadata tables:
  - `data_centers` (id, name, status, last_sync)
  - `ingestion_runs` (id, source_id, status, records_ingested, errors)
  - `schema_registry` (table, version, columns)

### Alerts Store
- `events`, `metrics`, `alert_history`, `anomaly_history`

### Dashboards Store
- `dashboards` (saved configurations)

### Scan History
- `scan_history` with JSON payloads and retention policy.

## Core Capabilities (Must Implement)
### 1) Automated Data Collection
- Configurable connectors per data center.
- Scheduled ingestion + incremental sync.
- Schema normalization and mapping into canonical tables.
- File/CSV ingestion endpoint and automated pickup.

### 2) Unified Analytics Engine
- NL2SQL with strict schema grounding.
- Clarification flow for ambiguous queries.
- Validation + repair loop.
- Safe SQL execution (read-only).
- Structured output: SQL, rows, visualization config, insights.

### 3) Sentinel Autonomous Agent
- Continuous scanning over consolidated data.
- Mission generation per domain (security, compliance, risk, ops).
- Risk scoring and correlation across data centers.
- Deep-dive follow-ups for anomalies.
- Executive narrative summary generation.
- Persistent scan history with SSE streaming updates.

### 4) Alerts & Monitoring
- Alert metrics CRUD.
- Sliding window evaluation (Redis optional, SQLite fallback).
- Event ingestion API.
- Anomaly summaries and spike detection.
- Automated alerting when data center issues detected.

### 5) Frontend UI
- Data center overview dashboard.
- Chat-style NL2SQL interface.
- Sentinel dashboard with risk visualization.
- Tables, charts, and CSV export.
- Environment/config panel.
- Streaming status indicator for ingestion and scans.

### 6) Deployment & Ops
- Dockerized backend and frontend.
- CI for tests + build.
- Environment-based config (dev/stage/prod).
- Structured logging, metrics, error handling.

## API Requirements (Must Build)
### Public API
- `GET /health`
- `POST /api/v1/query`
- `POST /api/v1/alert`
- `GET /api/v1/sentinel/scan`
- `GET /api/v1/sentinel/scan/stream`
- `GET /api/v1/sentinel/history`
- `GET /api/v1/sentinel/history/{scan_id}`
- `GET /api/v1/dashboards`
- `POST /api/v1/dashboards`
- `GET /api/v1/dashboards/{dashboardId}`

### Data Collection API
- `POST /api/v1/ingest/upload` (CSV file ingestion)
- `POST /api/v1/ingest/sync` (trigger sync for a data center)
- `GET /api/v1/ingest/status` (latest ingestion status)
- `GET /api/v1/data-centers` (list sources + health)

### Admin/Diagnostics
- `/api/db-test/*`
- `/redis-test/*`
- `/api/v1/alerts/*`

## Quality Bar
- Test coverage for ingestion, NL2SQL, and alerting.
- Deterministic SQL generation constraints.
- Consistent API error responses.
- Robust schema validation and safe query execution.

## Security Requirements (Deferred)
- Authentication and RBAC for production.
- Secrets management for connectors.
- Audit logging for all queries and scans.

## Milestones
1. Data source configuration + ingestion pipeline.
2. Centralized storage + schema registry.
3. NL2SQL + interactive queries over unified data.
4. Sentinel proactive agent + alerts.
5. Dashboards and UI polish.
6. CI/CD + deployment validation.

## Acceptance Criteria
- Data centers sync automatically with no manual intervention.
- Queries and dashboards operate on consolidated data.
- AI agent produces proactive insights and alerts.
- UI shows ingestion health, risk status, and analytics outputs.
