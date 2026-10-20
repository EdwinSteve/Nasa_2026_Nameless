from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.modules.identidad.domain.entity import Role, Sesion, User, UserStatus, Politica
from app.modules.identidad.domain.errors import EmailAlreadyRegistered, PhoneAlreadyRegistered
from app.modules.identidad.domain.values import Email, Phone
from app.modules.identidad.infrastructure.persistences.orm_models import (
    ConsentimientoORM,
    EventoAuthORM,
    PoliticaPrivacidadORM,
    SesionORM,
    UsuarioORM,
)


def _usuario_a_dominio(row: UsuarioORM) -> User:
    return User(
        id=row.id,
        phone=Phone(row.phone),
        email=Email(row.email) if row.email else None,
        password_hash=row.password_hash,
        role=Role(row.role),
        status=UserStatus(row.status),
        full_name=row.full_name,
        municipality=row.municipality,
        district=row.district,
        failed_attempts=row.failed_attempts,
        locked_until=row.locked_until,
        last_login_at=row.last_login_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _sesion_a_dominio(row: SesionORM) -> Sesion:
    return Sesion(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.refresh_token_hash,
        family_id=row.family_id,
        expires_at=row.expires_at,
        used_at=row.used_at,
        replaced_by=row.replaced_by,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._session.get(UsuarioORM, user_id)
        return _usuario_a_dominio(row) if row else None

    async def get_by_phone(self, phone: str) -> User | None:
        stmt = select(UsuarioORM).where(UsuarioORM.phone == phone)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _usuario_a_dominio(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UsuarioORM).where(UsuarioORM.email == email)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _usuario_a_dominio(row) if row else None

    async def save(self, user: User) -> User:
        row = await self._session.get(UsuarioORM, user.id)
        if row is None:
            row = UsuarioORM(id=user.id)
            self._session.add(row)
        row.phone = user.phone.value
        row.email = user.email.value if user.email else None  # el correo es opcional en el registro
        row.password_hash = user.password_hash
        row.role = user.role.value
        row.status = user.status.value
        row.full_name = user.full_name
        row.municipality = user.municipality
        row.district = user.district
        row.failed_attempts = user.failed_attempts
        row.locked_until = user.locked_until
        row.last_login_at = user.last_login_at
        try:
            await self._session.flush()
        except IntegrityError as exc:
            # Dos registros simultáneos con el mismo dato: gana el primero, el otro recibe 409.
            detalle = str(exc.orig)
            if "usuarios_phone_key" in detalle:
                raise PhoneAlreadyRegistered() from exc
            if "usuarios_email_key" in detalle:
                raise EmailAlreadyRegistered() from exc
            raise
        await self._session.refresh(row)
        return _usuario_a_dominio(row)


class SqlAlchemySesionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, sesion: Sesion) -> None:
        # flush aquí: la sesión nueva debe existir antes de que otra fila apunte a ella
        # con replaced_by (clave foránea).
        self._session.add(
            SesionORM(
                id=sesion.id,
                user_id=sesion.user_id,
                refresh_token_hash=sesion.token_hash,
                family_id=sesion.family_id,
                expires_at=sesion.expires_at,
                used_at=sesion.used_at,
                replaced_by=sesion.replaced_by,
                revoked_at=sesion.revoked_at,
            )
        )
        await self._session.flush()

    async def buscar_por_hash(self, token_hash: str) -> Sesion | None:
        return await self._buscar(token_hash, para_actualizar=False)

    async def buscar_por_hash_para_actualizar(self, token_hash: str) -> Sesion | None:
        return await self._buscar(token_hash, para_actualizar=True)

    async def _buscar(self, token_hash: str, *, para_actualizar: bool) -> Sesion | None:
        stmt = (
            select(SesionORM)
            .where(SesionORM.refresh_token_hash == token_hash)
            .execution_options(populate_existing=True)
        )
        if para_actualizar:
            stmt = stmt.with_for_update()
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _sesion_a_dominio(row) if row else None

    async def marcar_usada(self, sesion_id: UUID, reemplazada_por: UUID, ahora: datetime) -> None:
        await self._session.execute(
            update(SesionORM)
            .where(SesionORM.id == sesion_id)
            .values(used_at=ahora, replaced_by=reemplazada_por)
        )

    async def revocar(self, sesion_id: UUID, ahora: datetime) -> None:
        await self._session.execute(
            update(SesionORM)
            .where(SesionORM.id == sesion_id, SesionORM.revoked_at.is_(None))
            .values(revoked_at=ahora)
        )

    async def revocar_familia(self, family_id: UUID, ahora: datetime) -> None:
        await self._session.execute(
            update(SesionORM)
            .where(SesionORM.family_id == family_id, SesionORM.revoked_at.is_(None))
            .values(revoked_at=ahora)
        )

    async def revocar_todas_del_usuario(self, user_id: UUID, ahora: datetime) -> None:
        await self._session.execute(
            update(SesionORM)
            .where(SesionORM.user_id == user_id, SesionORM.revoked_at.is_(None))
            .values(revoked_at=ahora)
        )


class SqlAlchemyEventoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(self, evento: str, user_id: UUID | None, meta: dict | None = None) -> None:
        # Nunca se registran contraseñas, tokens ni celulares completos.
        self._session.add(EventoAuthORM(user_id=user_id, event=evento, meta=meta))
        await self._session.flush()

class SqlAlchemyPoliticaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self) -> Politica | None:
        stmt = select(PoliticaPrivacidadORM).where(PoliticaPrivacidadORM.is_active.is_(True))
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return Politica(id=row.id, version=row.version, contenido=row.content) if row else None


class SqlAlchemyConsentimientoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(self, user_id: UUID, policy_id: UUID, ahora: datetime) -> None:
        self._session.add(ConsentimientoORM(user_id=user_id, policy_id=policy_id, accepted_at=ahora))
        await self._session.flush()