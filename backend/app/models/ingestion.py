from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class DataCenter(Base):
    __tablename__ = "data_centers"
    __table_args__ = (
        Index("ix_data_centers_name", "name"),
        Index("ix_data_centers_status", "status"),
        Index("ix_data_centers_last_sync", "last_sync"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    status: Mapped[str] = mapped_column(String(50), default="healthy")
    last_sync: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        Index("ix_ingestion_runs_data_center_id", "data_center_id"),
        Index("ix_ingestion_runs_status", "status"),
        Index("ix_ingestion_runs_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data_center_id: Mapped[int | None] = mapped_column(ForeignKey("data_centers.id"), nullable=True)
    source_id: Mapped[str] = mapped_column(String(200), default="manual")
    status: Mapped[str] = mapped_column(String(50), default="running")
    records_ingested: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SchemaRegistry(Base):
    __tablename__ = "schema_registry"
    __table_args__ = (
        Index("ix_schema_registry_table_name", "table_name"),
        Index("ix_schema_registry_version", "version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_name: Mapped[str] = mapped_column(String(200))
    version: Mapped[int] = mapped_column(Integer, default=1)
    columns_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
