from typing import Optional
import sqlglot
from sqlglot import exp


def repair_sql(sql: str, default_limit: int = 100) -> Optional[str]:
    try:
        expression = sqlglot.parse_one(sql)
    except sqlglot.errors.ParseError:
        return None

    if isinstance(expression, exp.Select):
        if not expression.args.get("limit"):
            expression.set("limit", exp.Limit(this=exp.Literal.number(default_limit)))
    return expression.sql()
