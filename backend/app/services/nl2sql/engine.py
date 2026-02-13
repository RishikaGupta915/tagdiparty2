from typing import Any, Dict, List, Optional
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.services.nl2sql.schema import get_schema_profile
from app.services.nl2sql.validator import validate_sql
from app.services.nl2sql.repair import repair_sql
from app.services.nl2sql.graph import run_graph
from app.services.nl2sql.rules import generate_sql


def run_query_pipeline(db: Session, query: str, domain: Optional[str]) -> Dict[str, Any]:
    settings = get_settings()
    mode = settings.nl2sql_mode.lower()

    if mode in {"rules", "llm"}:
        state = run_graph(db, query, domain, mode)
        sql = state.get("sql")
        questions = state.get("questions", [])
        error = state.get("error")
    else:
        schema = get_schema_profile(db)
        sql, questions, _meta = generate_sql(query, domain, schema)
        error = validate_sql(sql) if sql else None
        if error:
            repaired = repair_sql(sql) if sql else None
            if repaired:
                sql = repaired
                error = validate_sql(sql)

    if not sql:
        return {
            "sql": None,
            "rows": [],
            "visualization": {"type": "table"},
            "insights": [],
            "clarification_needed": True,
            "clarification_questions": questions,
        }

    if error:
        return {
            "sql": sql,
            "rows": [],
            "visualization": {"type": "table"},
            "insights": [],
            "clarification_needed": False,
            "clarification_questions": [],
            "error": error,
        }

    rows = execute_sql(db, sql)
    meta = _build_meta_from_sql(sql)
    visualization = _suggest_visualization(meta)
    insights = _generate_insights(meta, rows)

    return {
        "sql": sql,
        "rows": rows,
        "visualization": visualization,
        "insights": insights,
        "clarification_needed": False,
        "clarification_questions": [],
    }


def _build_meta_from_sql(sql: str) -> Dict[str, Any]:
    text_lower = sql.lower()
    meta: Dict[str, Any] = {"intent": "list", "group_by": None}
    if "count(" in text_lower:
        meta["intent"] = "count"
    if "sum(" in text_lower:
        meta["intent"] = "sum"
    if "avg(" in text_lower:
        meta["intent"] = "avg"
    match = re.search(r"group by\s+(\w+)", text_lower)
    if match:
        meta["group_by"] = match.group(1)
    return meta


def _suggest_visualization(meta: Dict[str, Any]) -> Dict[str, Any]:
    intent = meta.get("intent")
    if meta.get("group_by"):
        return {"type": "bar", "x": meta.get("group_by"), "y": "count"}
    if intent in {"count", "sum", "avg"}:
        return {"type": "metric", "value": intent}
    return {"type": "table"}


def _generate_insights(meta: Dict[str, Any], rows: List[Dict[str, Any]]) -> List[str]:
    intent = meta.get("intent")
    if intent == "count" and rows:
        return [f"Count result: {rows[0].get('count')}"]
    if intent in {"sum", "avg"} and rows:
        key = "total_amount" if intent == "sum" else "avg_amount"
        return [f"{intent.upper()}(amount) = {rows[0].get(key)}"]
    return [f"Returned {len(rows)} rows."]


def execute_sql(db: Session, sql: str) -> List[Dict[str, Any]]:
    result = db.execute(text(sql))
    rows = [dict(r._mapping) for r in result]
    return rows
