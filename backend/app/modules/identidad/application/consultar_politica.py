from app.modules.identidad.domain.entity import Politica
from app.modules.identidad.domain.errors import PolicyUnavailable
from app.modules.identidad.domain.ports import PoliticaRepository


class ConsultarPoliticaVigente:
    """La UI la consulta al abrir el registro: la versión que devuelve es la que el
    productor acepta y la que después exige RegistrarUsuario."""

    def __init__(self, *, politicas: PoliticaRepository) -> None:
        self._politicas = politicas

    async def ejecutar(self) -> Politica:
        politica = await self._politicas.get_active()
        if politica is None:
            raise PolicyUnavailable()
        return politica
