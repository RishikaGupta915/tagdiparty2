from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    role: Mapped[str] = mapped_column(String(50), default="analyst")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    status: Mapped[str] = mapped_column(String(30), default="completed")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginEvent(Base):
    __tablename__ = "login_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    ip_address: Mapped[str] = mapped_column(String(45))
    success: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    event_metadata: Mapped[str] = mapped_column("metadata", Text, default="{}")
