import json
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.sentinel import ScanHistory
from app.services.nl2sql.engine import run_query_pipeline


DOMAIN_MISSIONS: Dict[str, List[Dict[str, Any]]] = {
    "security": [
        {"id": "failed_logins", "query": "Show recent failed logins", "risk_weight": 3},
        {"id": "flagged_transactions", "query": "List flagged transactions", "risk_weight": 4},
    ],
    "risk": [
        {"id": "high_value_transactions", "query": "List high value transactions", "risk_weight": 3},
        {"id": "failed_logins", "query": "Show recent failed logins", "risk_weight": 3},
    ],
    "operations": [
        {"id": "recent_logins", "query": "Show recent logins", "risk_weight": 1},
        {"id": "recent_transactions", "query": "List transactions", "risk_weight": 1},
    ],
    "compliance": [
        {"id": "all_users", "query": "List all users", "risk_weight": 1},
        {"id": "recent_logins", "query": "Show recent logins", "risk_weight": 1},
    ],
    "general": [
        {"id": "all_users", "query": "List users", "risk_weight": 1},
        {"id": "recent_transactions", "query": "List transactions", "risk_weight": 1},
    ],
}

DEEP_DIVE_QUERIES: Dict[str, str] = {
    "failed_logins": "Show failed logins by user_id",
    "flagged_transactions": "List flagged transactions by user_id",
    "high_value_transactions": "List transactions by user_id",
}


def _calc_risk(rows: List[Dict[str, Any]], weight: int) -> int:
    if not rows:
        return 0
    base = min(len(rows), 10)
    return base * weight


def _mission_result(db: Session, mission: Dict[str, Any], domain: str) -> Dict[str, Any]:
    result = run_query_pipeline(db, mission["query"], domain)
    if result.get("clarification_needed"):
        return {
            "mission_id": mission["id"],
            "mission": mission["query"],
            "status": "clarification",
            "questions": result.get("clarification_questions", []),
        }
    if result.get("error"):
        return {
            "mission_id": mission["id"],
            "mission": mission["query"],
            "status": "invalid",
            "error": result.get("error"),
        }

    rows = result.get("rows", [])
    risk = _calc_risk(rows, mission["risk_weight"])
    return {
        "mission_id": mission["id"],
        "mission": mission["query"],
        "status": "completed",
        "sql": result.get("sql"),
        "rows": rows,
        "risk": risk,
        "visualization": result.get("visualization"),
        "insights": result.get("insights"),
    }


def _deep_dive(db: Session, mission_id: str, domain: str) -> Optional[Dict[str, Any]]:
    follow_up = DEEP_DIVE_QUERIES.get(mission_id)
    if not follow_up:
        return None
    result = run_query_pipeline(db, follow_up, domain)
    if result.get("error") or result.get("clarification_needed"):
        return {
            "mission_id": f"{mission_id}_deep_dive",
            "mission": follow_up,
            "status": "skipped",
            "reason": result.get("error") or "clarification_needed",
        }
    return {
        "mission_id": f"{mission_id}_deep_dive",
        "mission": follow_up,
        "status": "completed",
        "sql": result.get("sql"),
        "rows": result.get("rows", []),
        "risk": 0,
        "visualization": result.get("visualization"),
        "insights": result.get("insights"),
    }


def _correlate(findings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    has_failed = any(f.get("mission_id") == "failed_logins" and f.get("risk", 0) > 0 for f in findings)
    has_flagged = any(f.get("mission_id") == "flagged_transactions" and f.get("risk", 0) > 0 for f in findings)
    if has_failed and has_flagged:
        return {
            "mission_id": "correlation_failed_flagged",
            "mission": "Correlate failed logins with flagged transactions",
            "status": "completed",
            "summary": "Failed logins and flagged transactions both present; investigate account compromise risk.",
            "risk": 10,
        }
    return None


def _narrative(domain: str, findings: List[Dict[str, Any]], risk_score: int) -> str:
    completed = len([f for f in findings if f.get("status") == "completed"])
    return (
        f"Sentinel scan completed for domain {domain}. "
        f"Completed {completed} missions with risk score {risk_score}."
    )


def run_scan(db: Session, domain: str) -> Dict[str, Any]:
    missions = DOMAIN_MISSIONS.get(domain, DOMAIN_MISSIONS["general"])
    findings: List[Dict[str, Any]] = []
    risk_score = 0

    for mission in missions:
        result = _mission_result(db, mission, domain)
        findings.append(result)
        risk_score += result.get("risk", 0)

        if result.get("risk", 0) >= 6:
            deep_dive = _deep_dive(db, mission["id"], domain)
            if deep_dive:
                findings.append(deep_dive)

    correlation = _correlate(findings)
    if correlation:
        findings.append(correlation)
        risk_score += correlation.get("risk", 0)

    scan_id = uuid.uuid4().hex
    result = {
        "scan_id": scan_id,
        "domain": domain,
        "status": "completed",
        "risk_score": risk_score,
        "findings": findings,
        "narrative": _narrative(domain, findings, risk_score),
    }

    history = ScanHistory(
        scan_id=scan_id,
        domain=domain,
        status="completed",
        risk_score=risk_score,
        result_json=json.dumps(result),
    )
    db.add(history)
    db.commit()

    return result


def run_scan_stream(db: Session, domain: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
    yield "status", {"status": "started", "domain": domain}

    missions = DOMAIN_MISSIONS.get(domain, DOMAIN_MISSIONS["general"])
    findings: List[Dict[str, Any]] = []
    risk_score = 0

    for mission in missions:
        yield "mission", {"mission_id": mission["id"], "status": "running"}
        result = _mission_result(db, mission, domain)
        findings.append(result)
        risk_score += result.get("risk", 0)
        yield "mission", {"mission_id": mission["id"], "status": result.get("status"), "risk": result.get("risk", 0)}

        if result.get("risk", 0) >= 6:
            deep_dive = _deep_dive(db, mission["id"], domain)
            if deep_dive:
                findings.append(deep_dive)
                yield "deep_dive", {"mission_id": deep_dive.get("mission_id"), "status": deep_dive.get("status")}

    correlation = _correlate(findings)
    if correlation:
        findings.append(correlation)
        risk_score += correlation.get("risk", 0)
        yield "correlation", {"status": "completed", "risk": correlation.get("risk", 0)}

    scan_id = uuid.uuid4().hex
    result = {
        "scan_id": scan_id,
        "domain": domain,
        "status": "completed",
        "risk_score": risk_score,
        "findings": findings,
        "narrative": _narrative(domain, findings, risk_score),
    }

    history = ScanHistory(
        scan_id=scan_id,
        domain=domain,
        status="completed",
        risk_score=risk_score,
        result_json=json.dumps(result),
    )
    db.add(history)
    db.commit()

    yield "complete", result


def list_history(db: Session) -> List[ScanHistory]:
    return list(db.execute(select(ScanHistory).order_by(ScanHistory.created_at.desc())).scalars())


def get_history(db: Session, scan_id: str) -> ScanHistory | None:
    return db.execute(select(ScanHistory).where(ScanHistory.scan_id == scan_id)).scalar_one_or_none()
