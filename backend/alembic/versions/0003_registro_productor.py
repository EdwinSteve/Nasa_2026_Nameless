"""registro de productor

Revision ID: 0003_registro_productor
Revises: 0002_rotacion_sesiones
Create Date: 2026-10-18 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_registro_productor"
down_revision = "0002_rotacion_sesiones"
branch_labels = None
depends_on = None

SCHEMA = "identidad"


def upgrade() -> None:
    # ADD VALUE se confirma aparte para que el valor nuevo quede disponible.
    with op.get_context().autocommit_block():
        op.execute(f"ALTER TYPE {SCHEMA}.rol_usuario ADD VALUE IF NOT EXISTS 'productor'")
        op.execute(f"ALTER TYPE {SCHEMA}.evento_auth ADD VALUE IF NOT EXISTS 'registro'")

    op.add_column("usuarios", sa.Column("full_name", sa.String(120), nullable=True), schema=SCHEMA)
    op.add_column("usuarios", sa.Column("municipality", sa.String(80), nullable=True), schema=SCHEMA)
    op.add_column("usuarios", sa.Column("district", sa.String(80), nullable=True), schema=SCHEMA)
    # El correo es opcional; el UNIQUE sigue y PostgreSQL permite varios NULL.
    op.alter_column("usuarios", "email", nullable=True, schema=SCHEMA)


def downgrade() -> None:
    # Falla si hay usuarios sin correo. Los valores de ENUM no se pueden quitar en PostgreSQL.
    op.alter_column("usuarios", "email", nullable=False, schema=SCHEMA)
    op.drop_column("usuarios", "district", schema=SCHEMA)
    op.drop_column("usuarios", "municipality", schema=SCHEMA)
    op.drop_column("usuarios", "full_name", schema=SCHEMA)