from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SCHEMA = "diagnostico"

CODIGO_VALUES = ("clima", "humedad", "suelo", "verdor")
ESTADO_VALUES = ("pendiente", "en_proceso", "lista", "fallida")
_ENUM_CODIGO = ENUM(*CODIGO_VALUES, name="codigo_paso", schema=SCHEMA, create_type=False)
_ENUM_ESTADO = ENUM(*ESTADO_VALUES, name="estado_paso", schema=SCHEMA, create_type=False)


class Base(DeclarativeBase):
    """La clave foránea tareas.lote_id → fincas.lotes existe en la migración 0005."""


class TareaORM(Base):
    __tablename__ = "tareas"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    lote_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PasoORM(Base):
    __tablename__ = "pasos"
    __table_args__ = ({"schema": SCHEMA},)

    tarea_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.tareas.id", ondelete="CASCADE"), primary_key=True
    )
    codigo: Mapped[str] = mapped_column(_ENUM_CODIGO, primary_key=True)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    estado: Mapped[str] = mapped_column(_ENUM_ESTADO, nullable=False, server_default="pendiente")
    iniciado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    terminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resumen: Mapped[str | None] = mapped_column(String(300), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    datos: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
