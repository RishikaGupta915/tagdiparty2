# PRD: Hackathon_backend_deriv (Implementation Plan)
Date: 2026-02-12
Status: Not implemented (new build required)

## What It Is
A FastAPI-based backend with a lightweight web UI that turns natural-language questions into SQL, executes queries against a financial dataset, and returns results with visualization hints and executive insights. It also includes an autonomous Sentinel scanning mode for proactive security/compliance/risk/operations monitoring, plus a full alerting subsystem with metrics, anomaly tracking, and synthetic event generation. Deployment is containerized and wired for AWS ECS.

## Summary
Build a full NL2SQL + Sentinel platform from scratch with a clear, modular architecture. This document defines what must be implemented in this repo.

## Goals
- Deliver a stable, maintainable NL2SQL + Sentinel backend and a minimal but functional frontend.
- Provide deterministic, safe SQL generation with schema grounding.
- Enable autonomous Sentinel scans with stored history and SSE streaming.
- Provide a working alerting subsystem with metrics, event ingestion, and anomaly history.
- Provide containerized deployment and CI scaffolding.

## Non-Goals
- Production-grade auth/RBAC, rate limiting, or hardened security.
- Multi-tenant data isolation.
- Arbitrary schema discovery without explicit configuration.

## Users
- Executive / Analyst
- Security / Compliance Lead
- Ops Engineer

## Tech Stack (Must Use)
- Backend: Python + FastAPI
- Frontend: React
- Orchestration: LangGraph + LangChain
- LLMs: Google Gemini (default), OpenAI (optional)
- Database: SQLite by default with `DATABASE_URL` overrides
- Deploy: Docker + GitHub Actions

## Data & Storage (Must Define)
- Primary DB schema for demo data (users, transactions, login_events).
- Alerts DB schema (events, metrics, alert_history, anomaly_history).
- Dashboards DB schema (dashboards).
- Scan history persistence format and retention strategy.

## Core Capabilities (Must Implement)
### 1) NL2SQL Query Engine
- Natural language to SQL generation with strict schema grounding.
- Clarification flow for ambiguous or unsupported queries.
- SQL validation and repair loop.
- Safe query execution with guardrails (read-only by default).
- Structured response: SQL, result data, visualization config, insights.

### 2) Domain Intelligence
- Domain-specific prompts and schema context.
- Configurable domains: security, compliance, risk, operations, general.
- Automated schema profiling to inform prompts and entity resolution.

### 3) Sentinel Autonomous Scanning
- Autonomous mission generation per domain.
- Mission execution pipeline using the NL2SQL engine.
- Risk scoring based on actual results.
- Deep-dive follow-ups for high-risk findings.
- Cross-domain correlation engine.
- Executive narrative summary generation.
- Scan history persistence and retrieval.
- Streaming scan endpoint (SSE) with progress events.

### 4) Alerting & Monitoring System
- Alert metrics CRUD (create/update/list/delete).
- Sliding window evaluation with fast cache (Redis/Valkey optional, SQLite fallback).
- Event ingestion API.
- Alert history and anomaly summaries.
- Event generators for testing and burst simulation.
- Worker registry and orchestration hooks.

### 5) Frontend UI
- Chat UI for NL2SQL queries.
- Sentinel dashboard for autonomous scan results.
- Charting and tabular results rendering.
- CSV export.
- API status indicator and environment configuration.

### 6) Deployment & Ops
- Dockerized backend and optional frontend hosting.
- CI workflow for backend tests and frontend build.
- Environment-based configuration (dev/stage/prod).
- Structured logging, metrics, and error handling.

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

### Admin/Diagnostics API
- `/api/db-test/*` (health, schema, tables, safe SELECT)
- `/redis-test/*` (ping, read-write, info)
- `/api/v1/alerts/*` (metrics, history, status, control)

## Quality Bar (Must Enforce)
- Test coverage for pipeline stages and key endpoints.
- Deterministic SQL generation constraints to prevent hallucinations.
- Clear error models and consistent API responses.
- Robust schema validation and query safety.

## Security Requirements (Deferred)
- Authentication and RBAC for production use.
- CORS configured per environment.
- Secrets management for API keys and tokens.
- Audit logging for all queries and scans.

## Milestones
1. Architecture & API contract finalized.
2. Core NL2SQL pipeline built and tested.
3. Sentinel scanning implemented.
4. Alert engine & metrics implemented.
5. Frontend UI and dashboard built.
6. CI/CD and deployment validated.

## Acceptance Criteria
- All required endpoints are implemented and documented.
- NL2SQL pipeline returns valid SQL and correct results for supported queries.
- Sentinel scans produce deterministic, explainable outputs and stored history.
- Alert engine can generate alerts from synthetic events.
- Frontend can query, visualize, and export results.
- CI/CD runs successfully.
