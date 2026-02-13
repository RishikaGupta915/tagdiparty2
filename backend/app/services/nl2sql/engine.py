from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.nl2sql.schema import get_schema_profile
from app.services.nl2sql.validator import validate_sql
from app.services.nl2sql.repair import repair_sql


TABLE_SYNONYMS = {
    "users": ["user", "users", "employee", "employees"],
    "transactions": ["transaction", "transactions", "payment", "payments"],
    "login_events": ["login", "logins", "auth", "authentication"],
}


def _detect_table(query: str, tables: List[str]) -> Optional[str]:
    q = query.lower()
    for table, aliases in TABLE_SYNONYMS.items():
        if table in tables and any(alias in q for alias in aliases):
            return table
    return None


def _detect_limit(query: str, default_limit: int = 100) -> int:
    match = re.search(r"top\s+(\d+)", query.lower())
    if match:
        return min(int(match.group(1)), 500)
    return default_limit


def _detect_group_by(query: str, columns: List[str]) -> Optional[str]:
    q = query.lower()
    for col in columns:
        if f"by {col}" in q:
            return col
    return None


def _detect_filters(query: str, table: str) -> List[str]:
    q = query.lower()
    filters: List[str] = []
    if table == "login_events" and ("failed" in q or "unsuccessful" in q):
        filters.append("success = 0")
    if table == "transactions" and ("flagged" in q or "suspicious" in q):
        filters.append("status = 'flagged'")
    return filters


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _detect_date_range(query: str) -> Optional[Tuple[str, str]]:
    q = query.lower()
    now = datetime.utcnow()

    if "today" in q:
        start = datetime(now.year, now.month, now.day)
        return _format_dt(start), _format_dt(now)

    if "yesterday" in q:
        end = datetime(now.year, now.month, now.day)
        start = end - timedelta(days=1)
        return _format_dt(start), _format_dt(end)

    if "this week" in q:
        start = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
        return _format_dt(start), _format_dt(now)

    if "this month" in q:
        start = datetime(now.year, now.month, 1)
        return _format_dt(start), _format_dt(now)

    match_days = re.search(r"(last|past)\s+(\d+)\s+days", q)
    if match_days:
        days = int(match_days.group(2))
        start = now - timedelta(days=days)
        return _format_dt(start), _format_dt(now)

    match_hours = re.search(r"(last|past)\s+(\d+)\s+hours", q)
    if match_hours:
        hours = int(match_hours.group(2))
        start = now - timedelta(hours=hours)
        return _format_dt(start), _format_dt(now)

    if "recent" in q:
        start = now - timedelta(days=7)
        return _format_dt(start), _format_dt(now)

    return None


def _detect_intent(query: str) -> str:
    q = query.lower()
    if "count" in q or "number of" in q:
        return "count"
    if "total" in q or "sum" in q:
        return "sum"
    if "average" in q or "avg" in q:
        return "avg"
    return "list"


def generate_sql(query: str, domain: Optional[str], schema: Dict[str, List[str]]) -> Tuple[Optional[str], List[str], Dict[str, Any]]:
    questions: List[str] = []
    meta: Dict[str, Any] = {"domain": domain, "intent": None, "table": None}

    table = _detect_table(query, list(schema.keys()))
    if not table:
        questions.append("Which dataset should I use: users, transactions, or login_events?")
        return None, questions, meta

    columns = schema[table]
    intent = _detect_intent(query)
    group_by = _detect_group_by(query, columns)
    filters = _detect_filters(query, table)
    limit = _detect_limit(query)
    date_range = _detect_date_range(query)

    if date_range and "created_at" in columns:
        start, end = date_range
        filters.append(f"created_at >= '{start}' AND created_at < '{end}'")

    meta.update(
        {
            "intent": intent,
            "table": table,
            "columns": columns,
            "group_by": group_by,
            "filters": filters,
            "limit": limit,
            "date_range": date_range,
        }
    )

    where_clause = f" WHERE {' AND '.join(filters)}" if filters else ""

    if group_by:
        if group_by not in columns:
            questions.append(f"Column '{group_by}' is not in {table}. Choose from: {', '.join(columns)}")
            return None, questions, meta
        sql = f"SELECT {group_by}, COUNT(*) AS count FROM {table}{where_clause} GROUP BY {group_by} ORDER BY count DESC"
        return sql, [], meta

    if intent == "count":
        sql = f"SELECT COUNT(*) AS count FROM {table}{where_clause}"
        return sql, [], meta

    if intent in {"sum", "avg"}:
        if "amount" not in columns:
            questions.append(f"'{table}' does not include an amount column. Choose a dataset with amounts.")
            return None, questions, meta
        metric = "SUM" if intent == "sum" else "AVG"
        alias = "total_amount" if intent == "sum" else "avg_amount"
        sql = f"SELECT {metric}(amount) AS {alias} FROM {table}{where_clause}"
        return sql, [], meta

    order_clause = ""
    if "recent" in query.lower() and "created_at" in columns:
        order_clause = " ORDER BY created_at DESC"

    sql = f"SELECT * FROM {table}{where_clause}{order_clause} LIMIT {limit}"
    return sql, [], meta


def run_query_pipeline(db: Session, query: str, domain: Optional[str]) -> Dict[str, Any]:
    schema = get_schema_profile(db)
    sql, questions, meta = generate_sql(query, domain, schema)

    if not sql:
        return {
            "sql": None,
            "rows": [],
            "visualization": {"type": "table"},
            "insights": [],
            "clarification_needed": True,
            "clarification_questions": questions,
        }

    error = validate_sql(sql)
    if error:
        repaired = repair_sql(sql)
        if repaired:
            sql = repaired
            error = validate_sql(sql)
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
