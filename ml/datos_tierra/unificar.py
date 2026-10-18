"""Une todas las fuentes de un lote en un solo JSON (esquema 2.0).

Compatible con el esquema 1.0 de unificated.py en las claves de primer nivel y en
los nombres power_*, smap_* e imerg_*. Lo nuevo: site, derived_*, composites, enso,
climatology y catalog_map. Ver ml/datos_tierra/README.md.
"""
import asyncio
from datetime import date, datetime, timedelta, timezone

import httpx

from . import SCHEMA_VERSION, derivadas, suelo
from .fuentes import dem, enso, imerg, modis, power, smap, soilgrids
from .fuentes.gee import FuenteOmitida

FUENTES = ('power', 'soilgrids', 'dem', 'enso', 'smap', 'imerg', 'modis')
FUENTES_SIN_GEE = ('power', 'soilgrids', 'dem', 'enso')
CLIMATOLOGIA_ANIOS = (1991, 2020)  # normal climatológica OMM
ENSO_MESES_PREVIOS = 12

# Desde cuándo existe cada columna: un vacío antes de esa fecha no es un dato faltante.
COBERTURA_COLUMNAS = {
    'smap_': smap.INICIO,
    'imerg_': imerg.INICIO,
    **{f'power_{p.lower()}': power.INICIO_RADIACION for p in power.PARAMETROS_RADIACION},
    'derived_et0_pm_mm': power.INICIO_RADIACION,
}

# Métrica del catálogo surco_agro -> campos de este JSON con que se compara
CATALOG_MAP = {
    'temperatura_aire_C': ['daily.derived_t2m_corr', 'daily.derived_t2m_max_corr', 'daily.derived_t2m_min_corr'],
    'precipitacion_mm': ['daily.derived_precip_mm'],
    'precipitacion_mm_dia': ['daily.derived_precip_mm'],
    'humedad_relativa_pct': ['daily.power_rh2m'],
    'viento_2m_ms': ['daily.power_ws2m'],
    'kc': ['daily.derived_et0_mm'],
    'agotamiento_permitido_p': ['daily.smap_sm_rootzone', 'soil.layers.*.wv0033', 'soil.layers.*.wv1500'],
    'N_O_CUL': ['soil.summary.0-30cm.nitrogen'],
    'ph': ['soil.summary.0-30cm.phh2o'],
    'altitud_msnm': ['site.elevation_m'],
}


def _a_fecha(valor: str | date) -> date:
    return valor if isinstance(valor, date) else date.fromisoformat(valor)


def _dias(inicio: date, fin: date) -> list[str]:
    return [(inicio + timedelta(days=i)).isoformat() for i in range((fin - inicio).days + 1)]


def _filas_power(series: dict, dias: list[str]) -> list[dict]:
    return [
        {'date': d, **{f'power_{p.lower()}': series.get(p, {}).get(d) for p in power.PARAMETROS}}
        for d in dias
    ]


def _cobertura_de(columna: str) -> date | None:
    for prefijo, desde in COBERTURA_COLUMNAS.items():
        if columna == prefijo or (prefijo.endswith('_') and columna.startswith(prefijo)):
            return desde
    return None


def _calidad(diario: list[dict], fuentes_pedidas: set[str]) -> dict:
    columnas = [c for c in diario[0] if c != 'date' and not c.endswith(('_source', '_method'))]
    faltantes, sin_cobertura = {}, {}
    for c in columnas:
        desde = _cobertura_de(c)
        vacios = [f['date'] for f in diario if f[c] is None]
        antes = sum(desde is not None and d < desde.isoformat() for d in vacios)
        faltantes[c] = len(vacios) - antes
        if antes:
            sin_cobertura[c] = antes
    return {
        'missing_days': faltantes,
        'outside_coverage_days': sin_cobertura,
        'imerg_share_of_precip': round(
            sum(f['derived_precip_source'] == 'imerg' for f in diario) / len(diario), 3
        ) if 'imerg' in fuentes_pedidas else 0.0,
    }


async def ejecutar(
    cliente: httpx.AsyncClient,
    lat: float,
    lon: float,
    inicio: str | date,
    fin: str | date,
    *,
    poligono: list[list[float]] | None = None,
    buffer_m: float = 5000,
    elevacion_m: float | None = None,
    fuentes: tuple[str, ...] = FUENTES,
    climatologia: bool = False,
    enso_texto: str | None = None,
) -> dict:
    """elevacion_m: si se conoce (registro del lote), evita consultar el DEM.
    enso_texto: tabla ONI ya descargada, para no pedirla una vez por punto en el modo masivo.
    """
    inicio, fin = _a_fecha(inicio), _a_fecha(fin)
    if fin < inicio:
        raise ValueError('La fecha final no puede ser anterior a la inicial.')
    pedidas = set(fuentes)
    desconocidas = pedidas - set(FUENTES)
    if desconocidas:
        raise ValueError(f'Fuentes desconocidas: {sorted(desconocidas)}. Opciones: {FUENTES}')

    c0, c1 = CLIMATOLOGIA_ANIOS
    climatologia_aparte = climatologia and not (inicio <= date(c0, 1, 1) and fin >= date(c1, 12, 31))
    tareas = {}
    if 'power' in pedidas or climatologia:
        tareas['power'] = power.descargar(cliente, lat, lon, inicio, fin)
    if climatologia_aparte:
        tareas['power_climatology'] = power.descargar(cliente, lat, lon, date(c0, 1, 1), date(c1, 12, 31))
    if 'soilgrids' in pedidas:
        tareas['soilgrids'] = soilgrids.descargar(cliente, lat, lon)
    if 'dem' in pedidas and elevacion_m is None:
        tareas['dem'] = dem.elevaciones(cliente, [(lat, lon)])
    if 'enso' in pedidas and enso_texto is None:
        tareas['enso'] = enso.descargar(cliente)
    for nombre, modulo in (('smap', smap), ('imerg', imerg), ('modis', modis)):
        if nombre in pedidas:
            tareas[nombre] = asyncio.to_thread(modulo.descargar, lat, lon, inicio, fin, poligono, buffer_m)

    resultados = await asyncio.gather(*tareas.values(), return_exceptions=True)  # una fuente caída no tumba las demás
    sources, datos, alertas = {}, {}, []
    for nombre, resultado in zip(tareas, resultados):
        if isinstance(resultado, FuenteOmitida):
            sources[nombre] = {'status': 'skipped', 'reason': str(resultado)}
        elif isinstance(resultado, Exception):
            sources[nombre] = {'status': 'error', 'error': f'{type(resultado).__name__}: {resultado}'}
        else:
            datos[nombre] = resultado
            sources[nombre] = {'status': 'ok'}
    if enso_texto is not None:
        datos['enso'] = enso_texto
        sources['enso'] = {'status': 'ok', 'cached': True}

    # --- Sitio y corrección de temperatura (ADR 0002)
    series_power, elevacion_celda = {}, None
    if 'power' in datos:
        series_power, meta = power.series(datos['power'])
        sources['power'].update(meta)
        elevacion_celda = meta['cell_elevation_m']

    fuente_elevacion = None
    if elevacion_m is not None:
        fuente_elevacion = 'usuario'
    elif 'dem' in datos and datos['dem'][0] is not None:
        elevacion_m, fuente_elevacion = datos['dem'][0], dem.FUENTE
        sources['dem'].update({'source': dem.FUENTE, 'endpoint': dem.URL})

    correccion = None
    if elevacion_celda is not None and elevacion_m is not None:
        correccion = round(derivadas.correccion_temperatura_c(elevacion_celda, elevacion_m), 2)
    else:
        alertas.append('Sin elevación del punto o de la celda: la temperatura NO se corrigió (ADR 0002).')
    z = elevacion_m if elevacion_m is not None else (elevacion_celda or 0.0)

    site = {
        'elevation_m': elevacion_m,
        'elevation_source': fuente_elevacion,
        'power_cell_elevation_m': elevacion_celda,
        'temperature_correction_c': correccion,
        'lapse_rate_c_per_km': derivadas.GRADIENTE_TERMICO_C_M * 1000,
        'land_cover': (datos.get('modis') or {}).get('land_cover'),
    }

    # --- Serie diaria
    dias = _dias(inicio, fin)
    diario = _filas_power(series_power, dias)
    sm = datos.get('smap')
    if sm:
        sources['smap'].update({k: sm[k] for k in ('source', 'collection', 'units', 'resolution_m', 'available_from')})
        sources['smap']['bands_missing'] = sm.get('bands_missing', [])
    columnas_smap = sm['bands'] if sm else list(dict.fromkeys(smap.BANDAS.values()))
    por_fecha_smap = {r['date']: r for r in sm['series']} if sm else {}
    im = datos.get('imerg')
    if im:
        sources['imerg'].update({k: im[k] for k in ('source', 'collection', 'units', 'resolution_m', 'available_from')})
    por_fecha_imerg = {r['date']: r['precip_mm'] for r in im['series']} if im else {}

    for fila in diario:
        if 'smap' in pedidas:
            for columna in columnas_smap:
                fila[f'smap_{columna}'] = por_fecha_smap.get(fila['date'], {}).get(columna)
        if 'imerg' in pedidas:
            fila['imerg_precip_mm'] = por_fecha_imerg.get(fila['date'])
        derivadas.agregar_derivadas(fila, correccion, z, lat)

    if 'power' in datos and inicio < power.INICIO_RADIACION:
        alertas.append('POWER no tiene radiación antes de 1984: en esos días la ET0 es Hargreaves.')

    # --- Suelo
    soil = None
    if 'soilgrids' in datos:
        soil = suelo.procesar(datos['soilgrids'])
        sources['soilgrids'].update({'endpoint': soilgrids.URL, 'depths': soilgrids.PROFUNDIDADES})
        if soil['empty']:
            alertas.append('SoilGrids devolvió el suelo vacío (zona urbana o cuerpo de agua).')

    # --- ENSO
    enso_filas = None
    if 'enso' in datos:
        desde = date(inicio.year, inicio.month, 1) - timedelta(days=31 * ENSO_MESES_PREVIOS)
        enso_filas = enso.filtrar(enso.parsear(datos['enso']), desde, fin)
        sources['enso'].update({'source': enso.FUENTE, 'endpoint': enso.URL})

    # --- Compuestos MODIS
    composites = None
    if 'modis' in datos:
        composites = {'modis_ndvi_16d': datos['modis']['ndvi'], 'modis_lst_8d': datos['modis']['lst']}
        sources['modis'].update({'source': datos['modis']['source'], 'available_from': datos['modis']['available_from']})

    # --- Climatología
    clima = None
    if climatologia:
        if climatologia_aparte and 'power_climatology' in datos:
            serie_clima, _ = power.series(datos['power_climatology'])
            filas_clima = _filas_power(serie_clima, _dias(date(c0, 1, 1), date(c1, 12, 31)))
            for fila in filas_clima:
                derivadas.agregar_derivadas(fila, correccion, z, lat)
        else:
            filas_clima = diario
        if filas_clima and any(f.get('power_t2m') is not None for f in filas_clima):
            clima = {
                'period': f'{c0}-{c1}',
                'window_days': 15,
                'note': 'Lluvia de POWER; temperatura corregida por elevación. Por día del año (365).',
                'by_day_of_year': derivadas.climatologia_diaria(filas_clima, c0, c1),
            }
        else:
            alertas.append('No se pudo calcular la climatología: falta la serie de POWER 1991-2020.')

    return {
        'schema_version': SCHEMA_VERSION,
        'fetched_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'location': {'lat': lat, 'lon': lon, 'polygon': poligono, 'buffer_m': None if poligono else buffer_m},
        'period': {'start': inicio.isoformat(), 'end': fin.isoformat(), 'days': len(dias)},
        'sources': sources,
        'site': site,
        'soil': soil,
        'daily': diario,
        'composites': composites,
        'enso': enso_filas,
        'climatology': clima,
        'quality': {**_calidad(diario, pedidas), 'alerts': alertas},
        'catalog_map': CATALOG_MAP,
    }
