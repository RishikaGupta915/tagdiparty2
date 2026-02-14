from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class TransactionArchive(Base):
    __tablename__ = "transactions_archive"
    __table_args__ = (
        Index("ix_transactions_archive_user_id", "user_id"),
        Index("ix_transactions_archive_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    status: Mapped[str] = mapped_column(String(30), default="completed")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginEventArchive(Base):
    __tablename__ = "login_events_archive"
    __table_args__ = (
        Index("ix_login_events_archive_user_id", "user_id"),
        Index("ix_login_events_archive_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    ip_address: Mapped[str] = mapped_column(String(45))
    success: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True))
    event_metadata: Mapped[str] = mapped_column("metadata", Text, default="{}")
    archived_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
