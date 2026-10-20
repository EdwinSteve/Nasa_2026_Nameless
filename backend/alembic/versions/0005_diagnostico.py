"""diagnóstico satelital del lote

Revision ID: 0005_diagnostico
Revises: 0004_fincas_lotes
Create Date: 2026-10-20 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_diagnostico"
down_revision = "0004_fincas_lotes"
branch_labels = None
depends_on = None

SCHEMA = "diagnostico"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    postgresql.ENUM("clima", "humedad", "suelo", "verdor", name="codigo_paso", schema=SCHEMA).create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM("pendiente", "en_proceso", "lista", "fallida", name="estado_paso", schema=SCHEMA).create(
        op.get_bind(), checkfirst=True
    )

    op.create_table(
        "tareas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "lote_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fincas.lotes.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )
    op.create_index("ix_tareas_lote", "tareas", ["lote_id"], schema=SCHEMA)

    # Una fila por paso: los cuatro se actualizan en paralelo sin pisarse.
    op.create_table(
        "pasos",
        sa.Column(
            "tarea_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{SCHEMA}.tareas.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("codigo", postgresql.ENUM(name="codigo_paso", schema=SCHEMA, create_type=False), primary_key=True),
        sa.Column("orden", sa.SmallInteger, nullable=False),
        sa.Column(
            "estado", postgresql.ENUM(name="estado_paso", schema=SCHEMA, create_type=False),
            nullable=False, server_default="pendiente",
        ),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terminado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resumen", sa.String(300), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("datos", postgresql.JSONB, nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("pasos", schema=SCHEMA)
    op.drop_index("ix_tareas_lote", table_name="tareas", schema=SCHEMA)
    op.drop_table("tareas", schema=SCHEMA)
    postgresql.ENUM(name="estado_paso", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="codigo_paso", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA}")
