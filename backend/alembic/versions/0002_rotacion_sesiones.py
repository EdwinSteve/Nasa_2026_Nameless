"""rotación de sesiones y último login

Revision ID: 0002_rotacion_sesiones
Revises: 0001_identidad_inicial
Create Date: 2026-10-17 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_rotacion_sesiones"
down_revision = "0001_identidad_inicial"
branch_labels = None
depends_on = None

SCHEMA = "identidad"


def upgrade() -> None:
    # Fecha del último login exitoso (ID-04).
    op.add_column(
        "usuarios",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )

    # used_at: el refresh token ya se canjeó (ID-05). Si vuelve a llegar, es reutilización.
    # replaced_by: enlaza el token viejo con el que lo reemplazó, para auditoría.
    op.add_column(
        "sesiones",
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "sesiones",
        sa.Column("replaced_by", postgresql.UUID(as_uuid=True), nullable=True),
        schema=SCHEMA,
    )
    op.create_foreign_key(
        "fk_sesiones_replaced_by",
        "sesiones",
        "sesiones",
        ["replaced_by"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="SET NULL",
    )

    # Búsqueda por hash en cada /refresh y /logout. Único para evitar colisiones.
    op.create_index(
        "uq_sesiones_refresh_hash",
        "sesiones",
        ["refresh_token_hash"],
        unique=True,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("uq_sesiones_refresh_hash", table_name="sesiones", schema=SCHEMA)
    op.drop_constraint(
        "fk_sesiones_replaced_by", "sesiones", schema=SCHEMA, type_="foreignkey"
    )
    op.drop_column("sesiones", "replaced_by", schema=SCHEMA)
    op.drop_column("sesiones", "used_at", schema=SCHEMA)
    op.drop_column("usuarios", "last_login_at", schema=SCHEMA)
