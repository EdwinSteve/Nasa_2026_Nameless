from uuid import uuid4

import pytest

from app.modules.fincas.application.casos import (
    CrearFinca,
    CrearLote,
    DatosFinca,
    DatosLote,
    GuardarPreferencias,
    ObtenerLote,
)
from app.modules.fincas.domain.entity import Prioridad
from app.modules.fincas.domain.errors import (
    FincaNoEncontrada,
    LoteNoEncontrado,
    PrioridadesInvalidas,
    RiegoInconsistente,
    UbicacionInvalida,
)
from tests.unit.fincas_fakes import (
    FORTALECILLAS,
    NEIVA,
    POLIGONO,
    FincasFalsas,
    LotesFalsos,
    PreferenciasFalsas,
    TerritorioFalso,
    UnitOfWorkFalso,
)

DUENO, OTRO = uuid4(), uuid4()
FINCA = DatosFinca(nombre="La Esperanza", municipio=NEIVA, corregimiento=FORTALECILLAS, vereda=None)
LOTE = DatosLote(nombre="La Vega", poligono=POLIGONO, tiene_riego=True, tipo_riego="goteo", cultivo_anterior="maiz")


class Entorno:
    def __init__(self) -> None:
        self.fincas, self.lotes, self.uow = FincasFalsas(), LotesFalsos(), UnitOfWorkFalso()
        self.preferencias = PreferenciasFalsas()
        self.crear_finca = CrearFinca(fincas=self.fincas, territorio=TerritorioFalso(), uow=self.uow)
        self.crear_lote = CrearLote(fincas=self.fincas, lotes=self.lotes, uow=self.uow)
        self.obtener_lote = ObtenerLote(fincas=self.fincas, lotes=self.lotes, territorio=TerritorioFalso())
        self.guardar = GuardarPreferencias(preferencias=self.preferencias, uow=self.uow)


@pytest.fixture
def e():
    return Entorno()


async def test_crear_finca_valida_la_ubicacion(e):
    finca = await e.crear_finca.ejecutar(DUENO, FINCA)

    assert finca.propietario_id == DUENO and finca.centro_poblado == FORTALECILLAS
    assert e.uow.confirmaciones == 1


@pytest.mark.parametrize("municipio, centro", [("41999", "41999001"), (NEIVA, "41132001")])
async def test_ubicacion_inexistente_o_que_no_corresponde(e, municipio, centro):
    with pytest.raises(UbicacionInvalida):
        await e.crear_finca.ejecutar(DUENO, DatosFinca("X", municipio, centro, None))


async def test_crear_lote_calcula_el_area_en_el_servidor(e):
    finca = await e.crear_finca.ejecutar(DUENO, FINCA)

    lote = await e.crear_lote.ejecutar(DUENO, finca.id, LOTE)

    assert lote.area_ha == pytest.approx(32.7395, rel=1e-4)
    assert lote.tipo_riego.value == "goteo"


async def test_lote_sin_riego_descarta_el_tipo(e):
    finca = await e.crear_finca.ejecutar(DUENO, FINCA)

    lote = await e.crear_lote.ejecutar(
        DUENO, finca.id, DatosLote("Seco", POLIGONO, tiene_riego=False, tipo_riego="goteo", cultivo_anterior=None)
    )

    assert lote.tipo_riego is None


async def test_lote_con_riego_sin_tipo(e):
    finca = await e.crear_finca.ejecutar(DUENO, FINCA)

    with pytest.raises(RiegoInconsistente):
        await e.crear_lote.ejecutar(DUENO, finca.id, DatosLote("X", POLIGONO, True, None, None))


async def test_nadie_crea_lotes_en_la_finca_de_otro(e):
    finca = await e.crear_finca.ejecutar(DUENO, FINCA)

    with pytest.raises(FincaNoEncontrada):
        await e.crear_lote.ejecutar(OTRO, finca.id, LOTE)
    with pytest.raises(FincaNoEncontrada):
        await e.crear_lote.ejecutar(DUENO, uuid4(), LOTE)


async def test_obtener_lote_con_nombres_y_solo_para_el_dueno(e):
    finca = await e.crear_finca.ejecutar(DUENO, FINCA)
    lote = await e.crear_lote.ejecutar(DUENO, finca.id, LOTE)

    detalle = await e.obtener_lote.ejecutar(DUENO, lote.id)

    assert (detalle.municipio_nombre, detalle.centro_poblado_nombre) == ("Neiva", "Fortalecillas")
    with pytest.raises(LoteNoEncontrado):
        await e.obtener_lote.ejecutar(OTRO, lote.id)


async def test_guardar_preferencias(e):
    orden = ["cuidar_suelo", "ahorro_agua", "arriesgar_menos", "ganar_mas"]

    preferencias = await e.guardar.ejecutar(DUENO, orden)

    assert preferencias.orden[0] is Prioridad.CUIDAR_SUELO
    assert e.preferencias.por_usuario[DUENO] == preferencias


@pytest.mark.parametrize(
    "orden",
    [
        ["ahorro_agua", "ahorro_agua", "ganar_mas", "cuidar_suelo"],
        ["ahorro_agua", "ganar_mas", "cuidar_suelo"],
        ["ahorro_agua", "ganar_mas", "cuidar_suelo", "volar"],
    ],
)
async def test_preferencias_deben_ser_las_cuatro_sin_repetir(e, orden):
    with pytest.raises(PrioridadesInvalidas):
        await e.guardar.ejecutar(DUENO, orden)
