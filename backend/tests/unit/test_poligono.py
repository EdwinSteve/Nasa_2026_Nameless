import math

import pytest

from app.modules.fincas.domain.errors import PoligonoInvalido
from app.modules.fincas.domain.values import RADIO_TIERRA_M, Poligono
from tests.unit.fincas_fakes import POLIGONO


def _poligono(*esquinas):
    anillo = [list(e) for e in esquinas]
    return {"type": "Polygon", "coordinates": [anillo + [anillo[0]]]}


def test_area_y_centroide_del_lote_de_fortalecillas():
    poligono = Poligono.desde_geojson(POLIGONO)

    # La fórmula del frontend (proyección local, src/lib/geo.ts) da 32,7395 ha para este lote
    assert poligono.area_ha == pytest.approx(32.7395, rel=1e-4)
    lat, lon = poligono.centroide
    assert lat == pytest.approx(2.9889, abs=1e-3) and lon == pytest.approx(-75.2912, abs=1e-3)


def test_un_cuadrado_de_100_m_de_lado_mide_una_hectarea():
    # En el ecuador de la esfera, 100 m son 100 / (R · π / 180) grados
    d = 100 / (RADIO_TIERRA_M * math.pi / 180)
    poligono = Poligono.desde_geojson(_poligono((-75.0, 0.0), (-75.0 + d, 0.0), (-75.0 + d, d), (-75.0, d)))

    assert poligono.area_ha == pytest.approx(1.0, rel=0.001)


def test_el_area_no_depende_del_sentido_de_las_esquinas():
    horario = Poligono.desde_geojson(POLIGONO)
    anillo = POLIGONO["coordinates"][0][::-1]
    antihorario = Poligono.desde_geojson({"type": "Polygon", "coordinates": [anillo]})

    assert antihorario.area_ha == pytest.approx(horario.area_ha)


def test_ida_y_vuelta_a_geojson():
    assert Poligono.desde_geojson(POLIGONO).a_geojson() == POLIGONO


@pytest.mark.parametrize(
    "geojson, mensaje",
    [
        ({"type": "Point", "coordinates": [-75, 3]}, "type = Polygon"),
        ({"type": "Polygon", "coordinates": [POLIGONO["coordinates"][0]] * 2}, "sin huecos"),
        ({"type": "Polygon", "coordinates": [[[-75.29, 2.99], [-75.28, 2.99], [-75.29, 2.99]]]}, "3 esquinas"),
        ({"type": "Polygon", "coordinates": [POLIGONO["coordinates"][0][:-1]]}, "cerrarse"),
        (_poligono((2.99, -75.29), (2.99, -75.28), (2.98, -75.28)), "fuera de Colombia"),
        # Un "moño": las esquinas en orden cruzado
        (_poligono((-75.29, 2.99), (-75.28, 2.98), (-75.28, 2.99), (-75.29, 2.98)), "se cruza"),
        (_poligono((-75.29, 2.99), (-75.29001, 2.99), (-75.29001, 2.99001)), "demasiado pequeño"),
        (_poligono((-75.9, 2.0), (-74.9, 2.0), (-74.9, 3.0), (-75.9, 3.0)), "demasiado grande"),
    ],
)
def test_poligonos_invalidos(geojson, mensaje):
    with pytest.raises(PoligonoInvalido, match=mensaje):
        Poligono.desde_geojson(geojson)
