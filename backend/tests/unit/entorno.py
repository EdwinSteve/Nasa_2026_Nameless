"""Entorno de identidad con todos los casos de uso conectados a los mismos dobles.

Así una prueba puede iniciar sesión y luego rotar o cerrar la sesión que acaba de crear,
y comprobar el efecto en el mismo almacén en memoria.
"""

from datetime import datetime, timezone

from app.modules.identidad.application.cerrar_sesion import CerrarSesion
from app.modules.identidad.application.iniciar_sesion import IniciarSesion
from app.modules.identidad.application.refrescar_sesion import RefrescarSesion
from app.modules.identidad.domain.entity import Role, User, UserStatus
from app.modules.identidad.domain.values import Email, Phone
from tests.unit.fakes import (
    EventosFalsos,
    GeneradorFalso,
    HasherFalso,
    RelojFalso,
    SesionesFalsas,
    TokensFalsos,
    UnitOfWorkFalso,
    UsuariosFalsos,
)

CELULAR_E164 = "+573001234567"
CONTRASENA = "MiFinca2026"
AHORA = datetime(2026, 10, 17, 10, 0, tzinfo=timezone.utc)


class EntornoIdentidad:
    def __init__(self, ahora: datetime = AHORA) -> None:
        self.usuarios = UsuariosFalsos()
        self.sesiones = SesionesFalsas()
        self.eventos = EventosFalsos()
        self.reloj = RelojFalso(ahora)
        self.uow = UnitOfWorkFalso()
        self.hasher = HasherFalso()
        self.generador = GeneradorFalso()
        self.tokens = TokensFalsos()

        self.usuario = User(
            phone=Phone(CELULAR_E164),
            email=Email("ana@finca.co"),
            password_hash=self.hasher.generate_hash(CONTRASENA),
            role=Role.APRENDIZ,
            status=UserStatus.ACTIVE,
        )
        self.usuarios.agregar(self.usuario)

        dependencias = dict(
            usuarios=self.usuarios,
            sesiones=self.sesiones,
            eventos=self.eventos,
            reloj=self.reloj,
            uow=self.uow,
            tokens=self.tokens,
            generador=self.generador,
        )
        self.iniciar = IniciarSesion(
            **dependencias,
            hasher=self.hasher,
            hash_ficticio=self.hasher.generate_hash("valor-ficticio"),
            max_intentos=5,
            bloqueo_minutos=15,
            dias_refresh=30,
        )
        self.refrescar = RefrescarSesion(**dependencias, dias_refresh=30)
        self.cerrar = CerrarSesion(
            sesiones=self.sesiones,
            eventos=self.eventos,
            generador=self.generador,
            reloj=self.reloj,
            uow=self.uow,
        )

    async def login(self):
        return await self.iniciar.ejecutar(CELULAR_E164, CONTRASENA)
