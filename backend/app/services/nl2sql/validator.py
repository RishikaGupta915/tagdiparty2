import re


def is_read_only_sql(sql: str) -> bool:
    statement = sql.strip().lower()
    if not statement.startswith("select"):
        return False
    banned = ["insert ", "update ", "delete ", "drop ", "alter ", "truncate "]
    return not any(token in statement for token in banned)


def has_single_statement(sql: str) -> bool:
    return ";" not in sql.strip().rstrip(";")
