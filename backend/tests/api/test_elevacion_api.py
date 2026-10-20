import httpx
import pytest

from app.api import app
from app.modules.territorio.api.dependencies import get_consultar_elevacion
from app.modules.territorio.application.consultas import ConsultarElevacion, distancia_km
from app.modules.territorio.infrastructure.divipola_json import DivipolaJsonRepository

RUTA = "/api/v1/territorio/elevacion"


class ModeloFalso:
    fuente = "NASA SRTM"

    def __init__(self, altitud=442.0, falla=False) -> None:
        self.altitud_m, self.falla = altitud, falla

    async def altitud(self, lat, lon):
        if self.falla:
            raise httpx.ConnectError("sin red")
        return self.altitud_m


def _caso(**kwargs) -> ConsultarElevacion:
    return ConsultarElevacion(territorio=DivipolaJsonRepository(), modelo=ModeloFalso(**kwargs))


async def _get(caso, **params):
    app.dependency_overrides[get_consultar_elevacion] = lambda: caso
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as cliente:
            return await cliente.get(RUTA, params=params)
    finally:
        app.dependency_overrides.clear()


def test_distancia_neiva_campoalegre_es_unos_30_km():
    assert distancia_km(2.9273, -75.2819, 2.6867, -75.3256) == pytest.approx(27, abs=3)


@pytest.mark.parametrize(
    "lat, lon, esperado",
    [
        (2.9889, -75.2912, "Neiva"),         # Fortalecillas
        (1.8533, -76.0511, "Pitalito"),
        (3.2200, -75.2200, "Villavieja"),
        (4.7110, -74.0721, None),            # Bogotá: fuera del Huila cargado
    ],
)
def test_municipio_mas_cercano(lat, lon, esperado):
    municipio = _caso().municipio_cercano(lat, lon)

    assert (municipio.nombre if municipio else None) == esperado


async def test_elevacion_con_municipio():
    respuesta = await _get(_caso(), lat=2.9889, lon=-75.2912)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "altitud_msnm": 442.0, "fuente": "NASA SRTM", "municipio_codigo": "41001", "municipio_nombre": "Neiva",
    }


async def test_fuera_del_huila_no_inventa_municipio():
    respuesta = await _get(_caso(), lat=4.711, lon=-74.0721)

    assert respuesta.json()["municipio_nombre"] is None


@pytest.mark.parametrize("params", [{"lat": 40.4, "lon": -3.7}, {"lat": 2.9}])
async def test_coordenadas_fuera_de_colombia_o_incompletas_responden_422(params):
    respuesta = await _get(_caso(), **params)

    assert respuesta.status_code == 422


@pytest.mark.parametrize("modelo", [{"falla": True}, {"altitud": None}])
async def test_sin_dato_responde_503(modelo):
    respuesta = await _get(_caso(**modelo), lat=2.9889, lon=-75.2912)

    assert respuesta.status_code == 503
    assert respuesta.json()["code"] == "TERRITORIO_ELEVACION_NO_DISPONIBLE"
