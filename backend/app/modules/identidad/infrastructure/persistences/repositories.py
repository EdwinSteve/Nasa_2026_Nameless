from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.domain.values import Email, Phone
from app.modules.identidad.infrastructure.persistences.orm_models import UsuarioORM


def _to_domain(row: UsuarioORM) -> User:
    return User(
        id=row.id,
        phone=Phone(row.phone),
        email=Email(row.email),
        password_hash=row.password_hash,
        role=Role(row.role),
        status=UserStatus(row.status),
        failed_attempts=row.failed_attempts,
        locked_until=row.locked_until,
        last_login_at=row.last_login_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._session.get(UsuarioORM, user_id)
        return _to_domain(row) if row else None

    async def get_by_phone(self, phone: str) -> User | None:
        stmt = select(UsuarioORM).where(UsuarioORM.phone == phone)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UsuarioORM).where(UsuarioORM.email == email)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def save(self, user: User) -> User:
        row = await self._session.get(UsuarioORM, user.id)
        if row is None:
            row = UsuarioORM(id=user.id)
            self._session.add(row)
        row.phone = user.phone.value
        row.email = user.email.value
        row.password_hash = user.password_hash
        row.role = user.role.value
        row.status = user.status.value
        row.failed_attempts = user.failed_attempts
        row.locked_until = user.locked_until
        row.last_login_at = user.last_login_at
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)