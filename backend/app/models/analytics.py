from sqlalchemy import DateTime, Float, Integer, String, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class DailyTransactionMetric(Base):
    __tablename__ = "daily_transaction_metrics"
    __table_args__ = (
        Index("ix_daily_transaction_metrics_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(10), unique=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    flagged_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
