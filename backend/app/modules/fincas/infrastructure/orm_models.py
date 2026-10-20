from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SCHEMA = "fincas"

TIPO_RIEGO_VALUES = ("gravedad", "aspersion", "goteo")
_ENUM_TIPO_RIEGO = ENUM(*TIPO_RIEGO_VALUES, name="tipo_riego", schema=SCHEMA, create_type=False)


class Base(DeclarativeBase):
    """Metadata propia del módulo. Las claves foráneas hacia identidad.usuarios
    existen en la base (migración 0004), pero no se declaran aquí para no acoplar
    las metadata de los dos módulos."""


class FincaORM(Base):
    __tablename__ = "fincas"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    propietario_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    municipio: Mapped[str] = mapped_column(String(5), nullable=False)
    centro_poblado: Mapped[str] = mapped_column(String(8), nullable=False)
    vereda: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LoteORM(Base):
    __tablename__ = "lotes"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    finca_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    poligono: Mapped[dict] = mapped_column(JSONB, nullable=False)
    area_ha: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    centroide_lat: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    centroide_lon: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    tiene_riego: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tipo_riego: Mapped[str | None] = mapped_column(_ENUM_TIPO_RIEGO, nullable=True)
    cultivo_anterior: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PreferenciasORM(Base):
    __tablename__ = "preferencias_productor"
    __table_args__ = ({"schema": SCHEMA},)

    usuario_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    orden: Mapped[list[str]] = mapped_column(ARRAY(String(20)), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

