from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyUnitOfWork:
    """Confirma la transacción de la operación en curso.

    La sesión de base de datos no hace commit sola: cada caso de uso decide cuándo
    confirmar, para que el login fallido también guarde el intento sumado antes de responder 401.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def confirmar(self) -> None:
        await self._session.commit()
