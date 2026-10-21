from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SCHEMA = "recomendacion"


class Base(DeclarativeBase):
    """La clave foránea lote_id → fincas.lotes existe en la migración 0006."""


class RecomendacionORM(Base):
    __tablename__ = "recomendaciones"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    lote_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    fecha_siembra: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(12), nullable=False)
    resultado: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    terminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
