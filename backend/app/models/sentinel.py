from sqlalchemy import DateTime, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ScanHistory(Base):
    __tablename__ = "scan_history"
    __table_args__ = (
        Index("ix_scan_history_domain", "domain"),
        Index("ix_scan_history_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[str] = mapped_column(String(64), unique=True)
    domain: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="completed")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
