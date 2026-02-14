from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


def archive_transactions(db: Session, before_date: str) -> int:
    insert_sql = text(
        """
        INSERT INTO transactions_archive (user_id, amount, currency, status, created_at)
        SELECT user_id, amount, currency, status, created_at
        FROM transactions
        WHERE created_at < :before_date
        """
    )
    delete_sql = text(
        """
        DELETE FROM transactions
        WHERE created_at < :before_date
        """
    )
    db.execute(insert_sql, {"before_date": before_date})
    result = db.execute(delete_sql, {"before_date": before_date})
    db.commit()
    return result.rowcount or 0


def archive_login_events(db: Session, before_date: str) -> int:
    insert_sql = text(
        """
        INSERT INTO login_events_archive (user_id, ip_address, success, created_at, metadata)
        SELECT user_id, ip_address, success, created_at, metadata
        FROM login_events
        WHERE created_at < :before_date
        """
    )
    delete_sql = text(
        """
        DELETE FROM login_events
        WHERE created_at < :before_date
        """
    )
    db.execute(insert_sql, {"before_date": before_date})
    result = db.execute(delete_sql, {"before_date": before_date})
    db.commit()
    return result.rowcount or 0


def refresh_daily_transaction_metrics(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
    where_clause = ""
    params = {}
    if start_date and end_date:
        where_clause = "WHERE created_at >= :start_date AND created_at < :end_date"
        params = {"start_date": start_date, "end_date": end_date}

    sql = text(
        f"""
        INSERT INTO daily_transaction_metrics (date, total_amount, transaction_count, flagged_count)
        SELECT
            substr(created_at, 1, 10) AS date,
            COALESCE(SUM(amount), 0) AS total_amount,
            COUNT(*) AS transaction_count,
            SUM(CASE WHEN status = 'flagged' THEN 1 ELSE 0 END) AS flagged_count
        FROM transactions
        {where_clause}
        GROUP BY substr(created_at, 1, 10)
        ON CONFLICT(date) DO UPDATE SET
            total_amount = excluded.total_amount,
            transaction_count = excluded.transaction_count,
            flagged_count = excluded.flagged_count
        """
    )
    result = db.execute(sql, params)
    db.commit()
    return result.rowcount or 0
