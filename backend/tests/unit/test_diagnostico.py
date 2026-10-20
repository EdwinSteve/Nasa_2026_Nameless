from datetime import timedelta
from uuid import uuid4

import pytest

from app.modules.diagnostico.application.casos import (
    ConsultarDiagnostico,
    EjecutarDiagnostico,
    IniciarDiagnostico,
    _mensaje_error,
)
from app.modules.diagnostico.domain import resumenes
from app.modules.diagnostico.domain.entity import (
    MENSAJE_FALLIDA,
    MENSAJE_INICIO,
    MENSAJE_LISTA,
    PASOS,
    CodigoPaso,
    EstadoPaso,
    Paso,
    Tarea,
)
from app.modules.diagnostico.domain.errors import DiagnosticoNoEncontrado, LoteSinAcceso
from tests.unit.diagnostico_fakes import (
    AHORA,
    DUENO,
    LOTE,
    LotesFalsos,
    ProveedorFalso,
    RelojFalso,
    TareasFalsas,
    UnitOfWorkFalso,
    fabrica,
)


# --- Frases para el productor ---------------------------------------------------

@pytest.mark.parametrize(
    "arena, limo, arcilla, clase",
    [
        (92, 5, 3, "Arenoso"),
        (40, 40, 20, "Franco"),
        (20, 65, 15, "Franco limoso"),
        (35, 35, 30, "Franco arcilloso"),
        (60, 10, 30, "Franco arcillo arenoso"),
        (15, 25, 60, "Arcilloso"),
        (65, 25, 10, "Franco arenoso"),
    ],
)
def test_textura_usda(arena, limo, arcilla, clase):
    assert resumenes.textura_usda(arena, limo, arcilla) == clase


def test_textura_normaliza_porcentajes_que_no_suman_100():
    assert resumenes.textura_usda(35.2, 35.6, 29.2) == resumenes.textura_usda(35.0, 35.8, 29.4)


def test_numeros_en_formato_colombiano():
    assert resumenes.numero(1255.4) == "1.255"
    assert resumenes.numero(27.64, 1) == "27,6"


def test_frases_de_cada_paso():
    assert resumenes.resumen_clima(1255.4, 27.64, 1981, 2025) == "1.255 mm de lluvia al año y 27,6 °C en promedio (1981–2025)"
    assert resumenes.resumen_humedad(0.165, 30) == "Tierra con humedad adecuada: 16 % de humedad en la zona de raíces (últimos 30 días)"
    assert resumenes.resumen_suelo(35, 35, 30, 5.6, 2.84) == "Franco arcilloso, pH 5,6 (ácido) y 2,8 % de materia orgánica"
    assert resumenes.resumen_verdor(0.631) == "NDVI 0,63: vegetación densa"


# --- Estados y avance -----------------------------------------------------------

def _tarea(*estados: EstadoPaso, iniciado=AHORA) -> Tarea:
    return Tarea(
        lote_id=LOTE.lote_id,
        pasos=[Paso(c, e, iniciado_en=iniciado if e is not EstadoPaso.PENDIENTE else None) for c, e in zip(CodigoPaso, estados)],
    )


def test_tarea_nueva_esta_pendiente():
    tarea = Tarea(lote_id=LOTE.lote_id)

    assert tarea.estado() is EstadoPaso.PENDIENTE
    assert tarea.progreso(AHORA) == 0
    assert tarea.mensaje() == MENSAJE_INICIO


def test_lista_si_termina_con_al_menos_un_paso_bueno():
    L, F = EstadoPaso.LISTA, EstadoPaso.FALLIDA
    assert _tarea(L, F, L, F).estado() is EstadoPaso.LISTA
    assert _tarea(L, F, L, F).mensaje() == MENSAJE_LISTA
    assert _tarea(F, F, F, F).estado() is EstadoPaso.FALLIDA
    assert _tarea(F, F, F, F).mensaje() == MENSAJE_FALLIDA


def test_en_proceso_muestra_la_frase_del_primer_paso_activo():
    L, E, P = EstadoPaso.LISTA, EstadoPaso.EN_PROCESO, EstadoPaso.PENDIENTE
    tarea = _tarea(L, P, E, E)

    assert tarea.estado() is EstadoPaso.EN_PROCESO
    assert tarea.paso_activo().codigo is CodigoPaso.SUELO
    assert tarea.mensaje() == PASOS[CodigoPaso.SUELO].frase


def test_el_avance_de_un_paso_sube_con_el_tiempo_sin_llegar_a_100():
    paso = Paso(CodigoPaso.SUELO, EstadoPaso.EN_PROCESO, iniciado_en=AHORA)

    assert paso.progreso(AHORA) == 5
    assert 5 < paso.progreso(AHORA + timedelta(seconds=30)) < 95
    assert paso.progreso(AHORA + timedelta(hours=1)) == 95


def test_un_paso_colgado_se_ve_como_fallido():
    limite = PASOS[CodigoPaso.CLIMA].tiempo_maximo_s
    tarea = _tarea(*[EstadoPaso.EN_PROCESO] * 4)

    tarde = tarea.vigente(AHORA + timedelta(seconds=limite + 120))

    assert tarde.pasos[0].estado is EstadoPaso.FALLIDA
    assert tarea.vigente(AHORA + timedelta(seconds=10)).pasos[0].estado is EstadoPaso.EN_PROCESO


# --- Casos de uso ---------------------------------------------------------------

async def test_iniciar_y_ejecutar_en_paralelo_guarda_cada_paso():
    tareas, proveedor = TareasFalsas(), ProveedorFalso()
    tarea, lote = await IniciarDiagnostico(lotes=LotesFalsos(), tareas=tareas, uow=UnitOfWorkFalso()).ejecutar(
        DUENO, LOTE.lote_id
    )

    await EjecutarDiagnostico(proveedor=proveedor, fabrica=fabrica(tareas), reloj=RelojFalso()).ejecutar(tarea.id, lote)

    guardada = tareas.por_id[tarea.id]
    assert [p.estado for p in guardada.pasos] == [EstadoPaso.LISTA] * 4
    assert guardada.pasos[2].resumen == "resumen de suelo"
    assert proveedor.max_en_vuelo == 4  # los cuatro pasos corrieron a la vez


async def test_un_paso_fallido_no_tumba_a_los_demas():
    tareas = TareasFalsas()
    tarea = await tareas.crear(Tarea(lote_id=LOTE.lote_id))

    await EjecutarDiagnostico(
        proveedor=ProveedorFalso(fallan=("humedad", "verdor")), fabrica=fabrica(tareas), reloj=RelojFalso()
    ).ejecutar(tarea.id, LOTE)

    guardada = tareas.por_id[tarea.id]
    assert [p.estado.value for p in guardada.pasos] == ["lista", "fallida", "lista", "fallida"]
    assert "humedad no disponible" in guardada.pasos[1].error
    assert guardada.estado() is EstadoPaso.LISTA


async def test_lote_ajeno_no_se_diagnostica():
    with pytest.raises(LoteSinAcceso):
        await IniciarDiagnostico(lotes=LotesFalsos(), tareas=TareasFalsas(), uow=UnitOfWorkFalso()).ejecutar(
            uuid4(), LOTE.lote_id
        )


async def test_consultar_valida_que_la_tarea_sea_de_ese_lote():
    tareas = TareasFalsas()
    ajena = await tareas.crear(Tarea(lote_id=uuid4()))
    consultar = ConsultarDiagnostico(lotes=LotesFalsos(), tareas=tareas, reloj=RelojFalso())

    with pytest.raises(DiagnosticoNoEncontrado):
        await consultar.ejecutar(DUENO, LOTE.lote_id, ajena.id)
    with pytest.raises(DiagnosticoNoEncontrado):
        await consultar.ejecutar(DUENO, LOTE.lote_id, uuid4())


def test_mensaje_de_error_por_tiempo_agotado():
    assert "tardó demasiado" in _mensaje_error(TimeoutError())
