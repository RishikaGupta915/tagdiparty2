from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.nl2sql.validator import is_read_only_sql, has_single_statement


def _route_query_to_table(query: str) -> Optional[str]:
    q = query.lower()
    if "user" in q:
        return "users"
    if "transaction" in q:
        return "transactions"
    if "login" in q or "auth" in q:
        return "login_events"
    return None


def generate_sql(query: str, domain: Optional[str]) -> Tuple[Optional[str], List[str]]:
    table = _route_query_to_table(query)
    if table is None:
        return None, ["Which dataset should I use: users, transactions, or login_events?"]
    sql = f"SELECT * FROM {table} LIMIT 100"
    return sql, []


def validate_sql(sql: str) -> Optional[str]:
    if not is_read_only_sql(sql):
        return "SQL must be read-only (SELECT statements only)."
    if not has_single_statement(sql):
        return "Only a single SQL statement is allowed."
    return None


def execute_sql(db: Session, sql: str) -> List[Dict[str, Any]]:
    result = db.execute(text(sql))
    rows = [dict(r._mapping) for r in result]
    return rows
