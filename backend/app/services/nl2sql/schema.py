from typing import Dict, List
from sqlalchemy import inspect
from sqlalchemy.orm import Session


def get_schema_profile(db: Session) -> Dict[str, List[str]]:
    inspector = inspect(db.bind)
    profile: Dict[str, List[str]] = {}
    for table in inspector.get_table_names():
        columns = inspector.get_columns(table)
        profile[table] = [column["name"] for column in columns]
    return profile
