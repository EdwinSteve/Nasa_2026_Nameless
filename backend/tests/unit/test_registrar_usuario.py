from dataclasses import replace
from uuid import uuid4

import pytest

from app.modules.identidad.application.dto import DatosRegistro
from app.modules.identidad.application.registrar_usuario import RegistrarUsuario
from app.modules.identidad.domain.entity import Politica, Role, UserStatus
from app.modules.identidad.domain.errors import (
    ConsentRequired,
    EmailAlreadyRegistered,
    PhoneAlreadyRegistered,
    PolicyOutdated,
)
from tests.unit.entorno import AHORA
from tests.unit.fakes import (
    ConsentimientosFalsos,
    EventosFalsos,
    GeneradorFalso,
    HasherFalso,
    PoliticasFalsas,
    RelojFalso,
    SesionesFalsas,
    TokensFalsos,
    UnitOfWorkFalso,
    UsuariosFalsos,
)

POLITICA = Politica(id=uuid4(), version="2026.1", contenido="Texto")

DATOS = DatosRegistro(
    full_name="Ernesto Ramírez",
    phone="300 123 4567",
    email=None,
    password="MiFinca2026",
    municipality="41001",
    district=None,
    accepts_policy=True,
    policy_version="2026.1",
)


class Entorno:
    def __init__(self, politica: Politica | None = POLITICA) -> None:
        self.usuarios = UsuariosFalsos()
        self.consentimientos = ConsentimientosFalsos()
        self.sesiones = SesionesFalsas()
        self.eventos = EventosFalsos()
        self.uow = UnitOfWorkFalso()
        self.caso = RegistrarUsuario(
            usuarios=self.usuarios,
            politicas=PoliticasFalsas(politica),
            consentimientos=self.consentimientos,
            sesiones=self.sesiones,
            eventos=self.eventos,
            hasher=HasherFalso(),
            tokens=TokensFalsos(),
            generador=GeneradorFalso(),
            reloj=RelojFalso(AHORA),
            uow=self.uow,
            dias_refresh=30,
        )


async def test_registro_sin_correo_crea_productor_activo_con_sesion():
    entorno = Entorno()

    resultado = await entorno.caso.ejecutar(DATOS)

    usuario = resultado.usuario
    assert usuario.email is None
    assert usuario.phone.value == "+573001234567"
    assert usuario.role is Role.PRODUCTOR
    assert usuario.status is UserStatus.ACTIVE
    assert usuario.password_hash != DATOS.password
    assert resultado.tokens.refresh_token and resultado.tokens.expira_en == 900
    assert len(entorno.sesiones.por_id) == 1
    assert entorno.consentimientos.registros == [(usuario.id, POLITICA.id, AHORA)]
    assert entorno.eventos.tipos() == ["registro"]
    assert entorno.uow.confirmaciones == 1


async def test_registro_con_correo_lo_normaliza_en_minusculas():
    resultado = await Entorno().caso.ejecutar(replace(DATOS, email="Ernesto@Finca.CO"))

    assert resultado.usuario.email.value == "ernesto@finca.co"


async def test_sin_consentimiento_no_guarda_nada():
    entorno = Entorno()

    with pytest.raises(ConsentRequired):
        await entorno.caso.ejecutar(replace(DATOS, accepts_policy=False))

    assert not entorno.usuarios.por_id
    assert entorno.uow.confirmaciones == 0


@pytest.mark.parametrize("politica", [None, Politica(id=uuid4(), version="2026.2")])
async def test_version_distinta_a_la_vigente_es_politica_desactualizada(politica):
    with pytest.raises(PolicyOutdated):
        await Entorno(politica).caso.ejecutar(DATOS)


async def test_celular_duplicado():
    entorno = Entorno()
    await entorno.caso.ejecutar(DATOS)

    with pytest.raises(PhoneAlreadyRegistered):
        await entorno.caso.ejecutar(replace(DATOS, phone="+573001234567"))


async def test_correo_duplicado():
    entorno = Entorno()
    await entorno.caso.ejecutar(replace(DATOS, email="ana@finca.co"))

    with pytest.raises(EmailAlreadyRegistered):
        await entorno.caso.ejecutar(replace(DATOS, phone="3109876543", email="ANA@finca.co"))
