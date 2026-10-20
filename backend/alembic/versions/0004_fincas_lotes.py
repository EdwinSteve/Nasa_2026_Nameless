"""fincas, lotes y preferencias del productor

Revision ID: 0004_fincas_lotes
Revises: 0003_registro_productor
Create Date: 2026-10-20 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_fincas_lotes"
down_revision = "0003_registro_productor"
branch_labels = None
depends_on = None

SCHEMA = "fincas"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    tipo_riego = postgresql.ENUM("gravedad", "aspersion", "goteo", name="tipo_riego", schema=SCHEMA)
    tipo_riego.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "fincas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "propietario_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identidad.usuarios.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("municipio", sa.String(5), nullable=False),
        sa.Column("centro_poblado", sa.String(8), nullable=False),
        sa.Column("vereda", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(r"municipio ~ '^\d{5}$'", name="ck_fincas_municipio_divipola"),
        sa.CheckConstraint(r"centro_poblado ~ '^\d{8}$' AND left(centro_poblado, 5) = municipio",
                           name="ck_fincas_centro_en_municipio"),
        schema=SCHEMA,
    )
    op.create_index("ix_fincas_propietario", "fincas", ["propietario_id"], schema=SCHEMA)

    op.create_table(
        "lotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "finca_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{SCHEMA}.fincas.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("nombre", sa.String(120), nullable=False),
        # GeoJSON tal cual; cuando se agregue PostGIS se puede derivar una columna geography.
        sa.Column("poligono", postgresql.JSONB, nullable=False),
        sa.Column("area_ha", sa.Numeric(12, 4), nullable=False),
        sa.Column("centroide_lat", sa.Numeric(9, 6), nullable=False),
        sa.Column("centroide_lon", sa.Numeric(9, 6), nullable=False),
        sa.Column("tiene_riego", sa.Boolean, nullable=False),
        sa.Column("tipo_riego", postgresql.ENUM(name="tipo_riego", schema=SCHEMA, create_type=False), nullable=True),
        sa.Column("cultivo_anterior", sa.String(60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("area_ha > 0", name="ck_lotes_area_positiva"),
        sa.CheckConstraint("tiene_riego OR tipo_riego IS NULL", name="ck_lotes_riego_consistente"),
        schema=SCHEMA,
    )
    op.create_index("ix_lotes_finca", "lotes", ["finca_id"], schema=SCHEMA)

    op.create_table(
        "preferencias_productor",
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identidad.usuarios.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("orden", postgresql.ARRAY(sa.String(20)), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("cardinality(orden) = 4", name="ck_preferencias_cuatro"),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("preferencias_productor", schema=SCHEMA)
    op.drop_index("ix_lotes_finca", table_name="lotes", schema=SCHEMA)
    op.drop_table("lotes", schema=SCHEMA)
    op.drop_index("ix_fincas_propietario", table_name="fincas", schema=SCHEMA)
    op.drop_table("fincas", schema=SCHEMA)
    postgresql.ENUM(name="tipo_riego", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA}")
