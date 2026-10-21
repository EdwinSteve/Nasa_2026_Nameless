"""recomendación de cultivos del modelo predictivo

Revision ID: 0006_recomendacion
Revises: 0005_diagnostico
Create Date: 2026-10-21 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_recomendacion"
down_revision = "0005_diagnostico"
branch_labels = None
depends_on = None

SCHEMA = "recomendacion"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.create_table(
        "recomendaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "lote_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fincas.lotes.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("fecha_siembra", sa.Date, nullable=False),
        sa.Column("estado", sa.String(12), nullable=False),
        # Lo que devuelve surco_ml.predecir.recomendar: un resultado por cultivo del catálogo
        sa.Column("resultado", postgresql.JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("terminado_en", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("estado IN ('en_proceso', 'lista', 'fallida')", name="ck_recomendaciones_estado"),
        sa.CheckConstraint("extract(day from fecha_siembra) IN (1, 16)", name="ck_recomendaciones_dia_siembra"),
        schema=SCHEMA,
    )
    op.create_index("ix_recomendaciones_lote", "recomendaciones", ["lote_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_recomendaciones_lote", table_name="recomendaciones", schema=SCHEMA)
    op.drop_table("recomendaciones", schema=SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA}")
