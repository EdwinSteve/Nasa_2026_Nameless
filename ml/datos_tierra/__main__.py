"""Línea de comandos. Ejecutar desde ml/:

    python -m datos_tierra lote --lat 3.22 --lon -75.22 --inicio 2024-01-01 --fin 2024-12-31 --climatologia
    python -m datos_tierra masivo --puntos ../data/fincas_demo.json --inicio 1981-01-01 --fin 2025-12-31
    python -m datos_tierra puntos --n 450 --n-huila 150 --out configs/puntos.csv
"""
import argparse
import asyncio
import csv
import gzip
import json
import os
import sys
import time
from pathlib import Path

import httpx

from . import suelo, unificar
from .fuentes import dem, enso, puntos, soilgrids, soilgrids_gee

RAIZ = Path(__file__).resolve().parents[2]
TIMEOUT = httpx.Timeout(300, connect=30)


def cargar_env(ruta: Path = RAIZ / '.env') -> None:
    """Carga el .env de la raíz sin pisar variables ya definidas (funciona igual en Linux y Windows)."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#') or '=' not in linea:
            continue
        clave, valor = linea.split('=', 1)
        valor = valor.strip().strip('"\'')
        if valor:
            os.environ.setdefault(clave.strip(), valor)


def _fuentes(texto: str) -> tuple[str, ...]:
    if texto == 'todas':
        return unificar.FUENTES
    if texto == 'sin-gee':
        return unificar.FUENTES_SIN_GEE
    return tuple(f.strip() for f in texto.split(',') if f.strip())


def _guardar(datos: dict, ruta: Path, comprimir: bool) -> None:
    """Escribe en un temporal y lo renombra: un corte a mitad de escritura no deja un archivo
    a medias que el modo masivo daría por descargado."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(ruta.name + '.tmp')
    if comprimir:
        with gzip.open(temporal, 'wt', encoding='utf-8') as fh:
            json.dump(datos, fh, ensure_ascii=False)
    else:
        temporal.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding='utf-8')
    os.replace(temporal, ruta)


def _resumen(datos: dict) -> str:
    estados = {k: v['status'] for k, v in datos['sources'].items()}
    faltantes = {k: v for k, v in datos['quality']['missing_days'].items() if v}
    sitio = datos['site']
    return (
        f"fuentes: {estados}\n"
        f"días: {datos['period']['days']} | elevación: {sitio['elevation_m']} m "
        f"(celda POWER {sitio['power_cell_elevation_m']} m, corrección {sitio['temperature_correction_c']} °C)\n"
        f"faltantes: {faltantes or 'ninguno'}\n"
        f"alertas: {datos['quality']['alerts'] or 'ninguna'}"
    )


def _leer_puntos(ruta: Path) -> list[dict]:
    """JSON con el formato de data/fincas_demo.json o CSV con columnas id,lat,lon[,elev_m]."""
    if ruta.suffix == '.json':
        contenido = json.loads(ruta.read_text(encoding='utf-8'))
        filas = contenido['fincas'] if isinstance(contenido, dict) else contenido
    else:
        with ruta.open(encoding='utf-8') as fh:
            filas = list(csv.DictReader(fh))
    return [
        {'id': str(f['id']), 'lat': float(f['lat']), 'lon': float(f['lon']),
         'elev_m': float(f['elev_m']) if f.get('elev_m') not in (None, '') else None}
        for f in filas
    ]


async def _lote(a) -> None:
    async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
        datos = await unificar.ejecutar(
            cliente, a.lat, a.lon, a.inicio, a.fin,
            buffer_m=a.buffer_m, elevacion_m=a.elevacion, fuentes=_fuentes(a.fuentes), climatologia=a.climatologia,
        )
    salida = Path(a.out) if a.out else RAIZ / f'data/processed/tierra_{a.lat}_{a.lon}_{a.inicio}_{a.fin}.json'
    _guardar(datos, salida, salida.suffix == '.gz')
    print(_resumen(datos))
    print('Guardado en', salida)


def _leer(ruta: Path) -> dict:
    with gzip.open(ruta, 'rt', encoding='utf-8') as fh:
        return json.load(fh)


async def _completar_suelo(cliente: httpx.AsyncClient, ruta: Path, via: str = 'rest') -> str:
    """Si SoilGrids falló o no se pidió en una descarga anterior, pide solo el suelo y lo agrega.

    El suelo no depende de las fechas, así que no hace falta repetir los 45 años de clima.
    Permite bajar primero el clima con --fuentes sin SoilGrids y completar el suelo después.
    via='gee' usa los mismos mapas publicados en Earth Engine cuando la API REST está caída.
    """
    datos = _leer(ruta)
    fuente = datos['sources'].get('soilgrids', {})
    if fuente.get('status') == 'ok':
        return 'ya existe, se salta'
    lat, lon = datos['location']['lat'], datos['location']['lon']
    try:
        if via == 'gee':
            crudo = await asyncio.to_thread(soilgrids_gee.descargar, lat, lon)
            meta = {'source': soilgrids_gee.FUENTE, 'via': 'earth_engine', 'note': 'solo la media; sin wv0033 ni wv1500'}
        else:
            crudo = await soilgrids.descargar(cliente, lat, lon)
            meta = {'endpoint': soilgrids.URL}
        procesado = suelo.procesar(crudo)
    except Exception as exc:
        return f'SoilGrids sigue fallando ({type(exc).__name__}); se reintenta en la próxima corrida'
    datos['soil'] = procesado
    datos['sources']['soilgrids'] = {'status': 'ok', **meta, 'depths': soilgrids.PROFUNDIDADES,
                                     'patched_at': time.strftime('%Y-%m-%dT%H:%M:%S')}
    if procesado['empty']:
        datos['quality']['alerts'].append('SoilGrids devolvió el suelo vacío (zona urbana o cuerpo de agua).')
    _guardar(datos, ruta, comprimir=True)
    return 'suelo completado'


async def _masivo(a) -> None:
    """Un archivo por punto; si ya existe se salta, así la descarga se puede reanudar.

    Al reanudar, los puntos a los que les falló SoilGrids solo vuelven a pedir el suelo.
    Si SoilGrids está caído: primero --fuentes power,smap,imerg,modis y luego, cuando vuelva,
    el mismo comando con --fuentes todas completa solo el suelo de cada punto.
    """
    lista = _leer_puntos(Path(a.puntos))
    destino = Path(a.dir)
    fuentes = _fuentes(a.fuentes)
    async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
        texto_enso = await enso.descargar(cliente)
        alturas = await dem.elevaciones(cliente, [(p['lat'], p['lon']) for p in lista])
        for i, (punto, altura) in enumerate(zip(lista, alturas), 1):
            ruta = destino / f"{punto['id']}.json.gz"
            if ruta.exists() and not a.forzar:
                estado = await _completar_suelo(cliente, ruta) if 'soilgrids' in fuentes else 'ya existe, se salta'
                print(f'[{i}/{len(lista)}] {punto["id"]}: {estado}', flush=True)
                continue
            t0 = time.monotonic()
            try:
                datos = await unificar.ejecutar(
                    cliente, punto['lat'], punto['lon'], a.inicio, a.fin,
                    elevacion_m=altura if altura is not None else punto['elev_m'],
                    fuentes=tuple(f for f in fuentes if f not in ('dem', 'enso')) + ('enso',),
                    enso_texto=texto_enso,
                )
            except Exception as exc:  # un punto malo no detiene la descarga
                print(f'[{i}/{len(lista)}] {punto["id"]}: ERROR {type(exc).__name__}: {exc}', file=sys.stderr, flush=True)
                continue
            # Si falló una fuente de clima, no se guarda: la próxima corrida lo repite completo.
            # SoilGrids es la excepción: se guarda y _completar_suelo lo arregla después.
            fallidas = [k for k, v in datos['sources'].items() if v['status'] == 'error' and k != 'soilgrids']
            if fallidas:
                print(f'[{i}/{len(lista)}] {punto["id"]}: ERROR en {fallidas}; no se guarda, se repite en la próxima corrida',
                      file=sys.stderr, flush=True)
                continue
            datos['site']['point_id'] = punto['id']
            if altura is not None:
                datos['site']['elevation_source'] = dem.FUENTE
            _guardar(datos, ruta, comprimir=True)
            estados = {k: v['status'] for k, v in datos['sources'].items()}
            print(f'[{i}/{len(lista)}] {punto["id"]}: {estados} ({time.monotonic() - t0:.0f} s)', flush=True)


async def _suelo(a) -> None:
    """Completa el suelo de los puntos ya descargados que no lo tienen."""
    archivos = sorted(Path(a.dir).glob('*.json.gz'))
    async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
        for i, ruta in enumerate(archivos, 1):
            print(f'[{i}/{len(archivos)}] {ruta.name.split(".")[0]}: {await _completar_suelo(cliente, ruta, a.via)}', flush=True)


def _puntos(a) -> None:
    lista = puntos.muestrear(a.n, a.n_huila, a.semilla)
    salida = Path(a.out)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open('w', newline='', encoding='utf-8') as fh:
        escritor = csv.DictWriter(fh, fieldnames=['id', 'lat', 'lon', 'zona'])
        escritor.writeheader()
        escritor.writerows(lista)
    print(f'{len(lista)} puntos guardados en {salida}')


def main() -> None:
    ap = argparse.ArgumentParser(prog='datos_tierra', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='comando', required=True)
    ayuda_fuentes = f"'todas', 'sin-gee' o una lista separada por comas de {', '.join(unificar.FUENTES)}"

    lote = sub.add_parser('lote', help='Un lote, un rango de fechas: JSON para el motor o la demo')
    lote.add_argument('--lat', type=float, default=3.22)
    lote.add_argument('--lon', type=float, default=-75.22)
    lote.add_argument('--inicio', default='2024-01-01')
    lote.add_argument('--fin', default='2024-12-31')
    lote.add_argument('--elevacion', type=float, default=None, help='Elevación conocida del lote (m); si falta se usa el DEM')
    lote.add_argument('--buffer-m', type=float, default=5000)
    lote.add_argument('--fuentes', default='todas', help=ayuda_fuentes)
    lote.add_argument('--climatologia', action='store_true', help='Agrega la climatología 1991-2020 por día del año')
    lote.add_argument('--out', default=None, help='Ruta de salida (.json o .json.gz)')

    masivo = sub.add_parser('masivo', help='Muchos puntos y rangos largos: insumo del entrenamiento')
    masivo.add_argument('--puntos', required=True, help='JSON como data/fincas_demo.json o CSV id,lat,lon[,elev_m]')
    masivo.add_argument('--inicio', default='1981-01-01')
    masivo.add_argument('--fin', default='2025-12-31')
    masivo.add_argument('--fuentes', default='todas', help=ayuda_fuentes)
    masivo.add_argument('--dir', default=str(RAIZ / 'data/raw/entrenamiento'))
    masivo.add_argument('--forzar', action='store_true', help='Volver a descargar aunque el archivo exista')

    sue = sub.add_parser('suelo', help='Completa el suelo de los puntos descargados sin SoilGrids')
    sue.add_argument('--dir', default=str(RAIZ / 'data/raw/entrenamiento'))
    sue.add_argument('--via', choices=('rest', 'gee'), default='rest',
                     help="rest: API de ISRIC (con cuantiles y agua retenida); gee: Earth Engine, si la API está caída")

    pts = sub.add_parser('puntos', help='Muestrea puntos de cultivo con MODIS Land Cover (requiere GEE)')
    pts.add_argument('--n', type=int, default=450, help='Puntos en el resto de Colombia')
    pts.add_argument('--n-huila', type=int, default=150)
    pts.add_argument('--semilla', type=int, default=7)
    pts.add_argument('--out', default=str(RAIZ / 'ml/configs/puntos.csv'))

    a = ap.parse_args()
    cargar_env()
    if a.comando == 'lote':
        asyncio.run(_lote(a))
    elif a.comando == 'masivo':
        asyncio.run(_masivo(a))
    elif a.comando == 'suelo':
        asyncio.run(_suelo(a))
    else:
        _puntos(a)


if __name__ == '__main__':
    main()
