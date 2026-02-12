from typing import Optional
import sqlglot
from sqlglot import exp


def is_read_only_sql(sql: str) -> bool:
    try:
        expression = sqlglot.parse_one(sql)
    except sqlglot.errors.ParseError:
        return False
    if not isinstance(expression, exp.Select):
        return False
    banned = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Truncate)
    return not expression.find(banned)


def has_single_statement(sql: str) -> bool:
    try:
        statements = sqlglot.parse(sql)
    except sqlglot.errors.ParseError:
        return False
    return len(statements) == 1


def validate_sql(sql: str) -> Optional[str]:
    if not has_single_statement(sql):
        return "Only a single SQL statement is allowed."
    if not is_read_only_sql(sql):
        return "SQL must be read-only (SELECT statements only)."
    return None
