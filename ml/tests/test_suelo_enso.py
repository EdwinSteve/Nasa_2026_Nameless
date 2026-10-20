import asyncio
from datetime import date

import httpx

from datos_tierra import suelo
from datos_tierra.fuentes import enso, soilgrids


def _capa(nombre, d_factor, target, valores_por_profundidad):
    rangos = {'0-5cm': (0, 5), '5-15cm': (5, 15), '15-30cm': (15, 30)}
    return {
        'name': nombre,
        'unit_measure': {'d_factor': d_factor, 'mapped_units': '', 'target_units': target},
        'depths': [
            {'label': etiqueta, 'range': {'top_depth': rangos[etiqueta][0], 'bottom_depth': rangos[etiqueta][1]},
             'values': valores}
            for etiqueta, valores in valores_por_profundidad.items()
        ],
    }


# Valores reales de Villavieja (3.22, -75.22), 0-5 cm, en unidades 'mapped'
CRUDO = {'properties': {'layers': [
    _capa('clay', 10, '%', {'0-5cm': {'mean': 292, 'Q0.05': 16, 'Q0.5': 241, 'Q0.95': 797},
                            '5-15cm': {'mean': 294, 'Q0.05': 20, 'Q0.5': 245, 'Q0.95': 800},
                            '15-30cm': {'mean': 300, 'Q0.05': 30, 'Q0.5': 250, 'Q0.95': 810}}),
    _capa('sand', 10, '%', {'0-5cm': {'mean': 352}, '5-15cm': {'mean': 350}, '15-30cm': {'mean': 340}}),
    _capa('silt', 10, '%', {'0-5cm': {'mean': 356}, '5-15cm': {'mean': 356}, '15-30cm': {'mean': 360}}),
    _capa('phh2o', 10, '-', {'0-5cm': {'mean': 56}, '5-15cm': {'mean': 56}, '15-30cm': {'mean': 58}}),
    _capa('wv0033', 10, '10-2 cm³/cm³', {'0-5cm': {'mean': 338}, '5-15cm': {'mean': 330}, '15-30cm': {'mean': 320}}),
    _capa('soc', 10, 'g/kg', {'0-5cm': {'mean': 222}, '5-15cm': {'mean': 150}, '15-30cm': {'mean': 100}}),
]}}


def test_convierte_unidades_y_agua_a_m3_m3():
    procesado = suelo.procesar(CRUDO)
    capa = procesado['layers']['0-5cm']['properties']
    assert capa['clay']['mean'] == 29.2
    assert capa['phh2o']['mean'] == 5.6
    assert capa['wv0033']['mean'] == 0.338
    assert procesado['units']['wv0033'] == 'm3/m3'
    assert procesado['empty'] is False


def test_promedio_ponderado_por_espesor():
    capas, _ = suelo.capas(CRUDO)
    # (5·5,8 ... ) -> pH: (5·5,6 + 10·5,6 + 15·5,8) / 30
    assert suelo.promedio_hasta(capas, 'phh2o', 30) == round((5 * 5.6 + 10 * 5.6 + 15 * 5.8) / 30, 4)
    # Hasta 10 cm solo pesan 5 cm de cada una de las dos primeras capas
    assert suelo.promedio_hasta(capas, 'clay', 10) == round((29.2 + 29.4) / 2, 4)


def test_control_de_textura_usa_la_media_no_cuantiles():
    assert suelo.procesar(CRUDO)['texture_sum_pct']['0-5cm'] == 100.0


def test_resumen_trae_materia_organica_e_incertidumbre():
    tramo = suelo.procesar(CRUDO)['summary']['0-30cm']
    assert tramo['organic_matter_pct'] > 0
    assert tramo['clay']['rel_uncertainty'] > 1  # SoilGrids es muy incierto en este punto


TEXTO_ONI = """ SEAS  YR   TOTAL   ANOM
  DJF 1950  25.01  -1.32
  JJA 2026  29.09   1.80
  JAS 2026  29.12   2.16
"""


def test_parsea_oni_y_clasifica_fase():
    filas = enso.parsear(TEXTO_ONI)
    assert filas[0] == {'season': 'DJF', 'year': 1950, 'month': 1, 'oni': -1.32, 'phase': 'la_nina'}
    assert filas[-1]['phase'] == 'el_nino'
    assert len(enso.filtrar(filas, date(2026, 1, 1), date(2026, 7, 31))) == 1


def test_soilgrids_parte_la_consulta_en_bloques_y_une_las_capas():
    pedidas = []

    def responder(request: httpx.Request) -> httpx.Response:
        props = request.url.params.get_list('property')
        pedidas.append(props)
        return httpx.Response(200, json={'properties': {'layers': [{'name': p} for p in props]}})

    async def correr():
        async with httpx.AsyncClient(transport=httpx.MockTransport(responder)) as cliente:
            return await soilgrids.descargar(cliente, 3.2, -75.2, propiedades=['a', 'b', 'c', 'd', 'e'], por_consulta=2)

    unida = asyncio.run(correr())

    assert pedidas == [['a', 'b'], ['c', 'd'], ['e']]
    assert [capa['name'] for capa in unida['properties']['layers']] == ['a', 'b', 'c', 'd', 'e']
