"""identidad inicial

Revision ID: 0001_identidad_inicial
Revises:
Create Date: 2026-01-15 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_identidad_inicial"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = "identidad"


# --- Definiciones de ENUM reutilizables (create_type=False) ---
def _enum_rol() -> postgresql.ENUM:
    return postgresql.ENUM(
        "aprendiz", "instructor", "admin",
        name="rol_usuario", schema=SCHEMA,
        create_type=False,  # ← clave: no lo auto-crea al usarlo en columnas
    )


def _enum_estado() -> postgresql.ENUM:
    return postgresql.ENUM(
        "activo", "inactivo", "bloqueado", "pendiente",
        name="estado_usuario", schema=SCHEMA,
        create_type=False,
    )


def _enum_evento() -> postgresql.ENUM:
    return postgresql.ENUM(
        "login_exitoso", "login_fallido", "logout",
        "refresh", "bloqueo", "desbloqueo",
        name="evento_auth", schema=SCHEMA,
        create_type=False,
    )


def upgrade() -> None:
    # --- Extensiones y esquema ---
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")

    # --- Enums (idempotente: no falla si ya existen) ---
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE {SCHEMA}.rol_usuario AS ENUM ('aprendiz','instructor','admin');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE {SCHEMA}.estado_usuario AS ENUM ('activo','inactivo','bloqueado','pendiente');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE {SCHEMA}.evento_auth AS ENUM
                ('login_exitoso','login_fallido','logout','refresh','bloqueo','desbloqueo');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    rol = _enum_rol()
    estado = _enum_estado()
    evento = _enum_evento()

    # --- usuarios ---
    op.create_table(
        "usuarios",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", rol, nullable=False),
        sa.Column("status", estado, nullable=False, server_default="pendiente"),
        sa.Column("failed_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            r"phone ~ '^\+[1-9][0-9]{7,14}$'",
            name="ck_usuarios_celular_e164",
        ),
        sa.CheckConstraint("failed_attempts >= 0", name="ck_usuarios_intentos"),
        schema=SCHEMA,
    )
    op.create_index("ix_usuarios_role", "usuarios", ["role"], schema=SCHEMA)
    op.create_index("ix_usuarios_status", "usuarios", ["status"], schema=SCHEMA)

    # --- politicas_privacidad ---
    op.create_table(
        "politicas_privacidad",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("version", sa.String(20), nullable=False, unique=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_politicas_vigente",
        "politicas_privacidad",
        ["is_active"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("is_active = true"),
    )

    # --- consentimientos ---
    op.create_table(
        "consentimientos",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{SCHEMA}.usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "policy_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{SCHEMA}.politicas_privacidad.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.UniqueConstraint("user_id", "policy_id", name="uq_consent_user_policy"),
        schema=SCHEMA,
    )

    # --- sesiones ---
    op.create_table(
        "sesiones",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{SCHEMA}.usuarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )
    op.create_index("ix_sesiones_family", "sesiones", ["family_id"], schema=SCHEMA)
    op.create_index("ix_sesiones_user", "sesiones", ["user_id"], schema=SCHEMA)

    # --- eventos_auth ---
    op.create_table(
        "eventos_auth",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{SCHEMA}.usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event", evento, nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_eventos_user_created",
        "eventos_auth",
        ["user_id", "created_at"],
        schema=SCHEMA,
    )

    # --- Semilla: política vigente 2026.1 ---
    op.execute(
        f"""
        INSERT INTO {SCHEMA}.politicas_privacidad (version, content, is_active)
        VALUES (
            '2026.1',
            'Texto pendiente por el equipo legal. Versión preliminar.',
            true
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_eventos_user_created", table_name="eventos_auth", schema=SCHEMA)
    op.drop_table("eventos_auth", schema=SCHEMA)

    op.drop_index("ix_sesiones_user", table_name="sesiones", schema=SCHEMA)
    op.drop_index("ix_sesiones_family", table_name="sesiones", schema=SCHEMA)
    op.drop_table("sesiones", schema=SCHEMA)

    op.drop_table("consentimientos", schema=SCHEMA)

    op.drop_index("uq_politicas_vigente", table_name="politicas_privacidad", schema=SCHEMA)
    op.drop_table("politicas_privacidad", schema=SCHEMA)

    op.drop_index("ix_usuarios_status", table_name="usuarios", schema=SCHEMA)
    op.drop_index("ix_usuarios_role", table_name="usuarios", schema=SCHEMA)
    op.drop_table("usuarios", schema=SCHEMA)

    # Enums
    for nombre in ("rol_usuario", "estado_usuario", "evento_auth"):
        op.execute(f"DROP TYPE IF EXISTS {SCHEMA}.{nombre}")

    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")