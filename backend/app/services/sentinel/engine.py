import json
import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.sentinel import ScanHistory
from app.services.nl2sql.engine import generate_sql, validate_sql, execute_sql


DOMAIN_MISSIONS = {
    "security": [
        "Show recent failed logins",
        "List flagged transactions",
    ],
    "risk": [
        "List high value transactions",
        "Show recent failed logins",
    ],
    "operations": [
        "Show recent logins",
        "List transactions",
    ],
    "compliance": [
        "List all users",
        "Show recent logins",
    ],
    "general": [
        "List users",
        "List transactions",
    ],
}


def run_scan(db: Session, domain: str) -> Dict[str, Any]:
    missions = DOMAIN_MISSIONS.get(domain, DOMAIN_MISSIONS["general"])
    findings: List[Dict[str, Any]] = []
    risk_score = 0

    for mission in missions:
        sql, clarifications = generate_sql(mission, domain)
        if not sql:
            findings.append({"mission": mission, "status": "clarification", "questions": clarifications})
            continue
        error = validate_sql(sql)
        if error:
            findings.append({"mission": mission, "status": "invalid", "error": error})
            continue
        rows = execute_sql(db, sql)
        score = 10 if rows else 0
        risk_score += score
        findings.append({"mission": mission, "status": "completed", "sql": sql, "rows": rows, "risk": score})

    scan_id = uuid.uuid4().hex
    narrative = f"Completed {len(findings)} missions for domain {domain}."
    result = {
        "scan_id": scan_id,
        "domain": domain,
        "status": "completed",
        "risk_score": risk_score,
        "findings": findings,
        "narrative": narrative,
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


def list_history(db: Session) -> List[ScanHistory]:
    return list(db.execute(select(ScanHistory).order_by(ScanHistory.created_at.desc())).scalars())


def get_history(db: Session, scan_id: str) -> ScanHistory | None:
    return db.execute(select(ScanHistory).where(ScanHistory.scan_id == scan_id)).scalar_one_or_none()
