"""Construye el dataset en Parquet, un par de archivos por punto (reanudable).

    python -m surco_ml.dataset                    # procesa los puntos ya descargados
    python -m surco_ml.dataset --forzar           # rehace todo (por ejemplo, si cambió el catálogo)

Salida en data/processed/dataset/:
  cultivos.parquet          una fila por cultivo: la ficha del catálogo como features (c_*)
  lote_fecha/<id>.parquet   una fila por fecha de siembra: features del día de la siembra (f_*)
  etiquetas/<id>.parquet    una fila por fecha × cultivo: etiquetas del oráculo y línea base
  manifiesto.json           versión de cada cultivo y parámetros, para registrar en MLflow

La tabla de entrenamiento (fecha × cultivo × features) no se guarda entera: se arma por lotes
al entrenar (modelos/gbdt.py), así no se duplican las features 44 veces en disco ni en RAM.
"""
import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import polars as pl

from . import catalogo
from .features import construir
from .oraculo import etiquetas, simulador
from .rutas import ANIOS, CRUDOS, DATASET, RAIZ
from .series import cargar

PUNTOS_CSV = RAIZ / 'ml/configs/puntos.csv'


def zonas(ruta: Path = PUNTOS_CSV) -> dict[str, str]:
    if not ruta.exists():
        return {}
    with ruta.open(encoding='utf-8') as fh:
        return {f['id']: f['zona'] for f in csv.DictReader(fh)}


def procesar_punto(ruta: Path, cultivos, salida: Path, zona: str | None) -> int:
    serie = cargar(ruta)
    e = etiquetas.etiquetar(serie, cultivos)
    s, c = e['puntaje'].shape

    feats = construir.construir(serie, e)
    lote = pl.DataFrame({
        'punto': [serie.id] * s, 'zona': [zona or 'desconocida'] * s,
        'anio': e['anio'].astype(np.int16), 'mes': e['mes'].astype(np.int8),
        'dia': e['dia'].astype(np.int8), 'ranura': e['ranura'].astype(np.int8),
        **{k: v.astype(np.float32) for k, v in feats.items()},
    })
    lote.write_parquet(salida / 'lote_fecha' / f'{serie.id}.parquet')

    columnas_sc = [k for k in e if isinstance(e[k], np.ndarray) and e[k].shape == (s, c)]
    tabla = {
        'fila': np.repeat(np.arange(s, dtype=np.int32), c),
        'cultivo': np.tile(np.arange(c, dtype=np.int8), s),
        'anio': np.repeat(e['anio'].astype(np.int16), c),
        'pc_taw_mm': np.tile(e['taw_mm'].astype(np.float32), s),
        **{k: e[k].reshape(-1).astype(np.float32) for k in columnas_sc},
    }
    df = pl.DataFrame(tabla).filter(pl.col('puntaje').is_not_nan())
    df.write_parquet(salida / 'etiquetas' / f'{serie.id}.parquet')
    return len(df)


def main() -> None:
    ap = argparse.ArgumentParser(prog='surco_ml.dataset', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--crudos', default=str(CRUDOS))
    ap.add_argument('--salida', default=str(DATASET))
    ap.add_argument('--forzar', action='store_true')
    a = ap.parse_args()

    salida = Path(a.salida)
    for sub in ('lote_fecha', 'etiquetas'):
        (salida / sub).mkdir(parents=True, exist_ok=True)
    lista = catalogo.cargar()
    cultivos = catalogo.a_arreglos(lista)
    pl.DataFrame({'cultivo': np.arange(len(lista), dtype=np.int8), 'cultivo_id': cultivos.ids,
                  **catalogo.features(lista)}).write_parquet(salida / 'cultivos.parquet')
    (salida / 'manifiesto.json').write_text(json.dumps({
        'cultivos': dict(zip(cultivos.ids, cultivos.version)),
        'anios': ANIOS, 'umbral_falla': simulador.UMBRAL_FALLA,
        'dias_arranque': simulador.DIAS_ARRANQUE, 'ventanas': construir.VENTANAS,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    por_zona = zonas()
    archivos = sorted(Path(a.crudos).glob('*.json.gz'))
    total = 0
    for i, ruta in enumerate(archivos, 1):
        pid = ruta.name.split('.')[0]
        destino = salida / 'etiquetas' / f'{pid}.parquet'
        if destino.exists() and not a.forzar and destino.stat().st_mtime > ruta.stat().st_mtime:
            continue
        t0 = time.monotonic()
        try:
            filas = procesar_punto(ruta, cultivos, salida, por_zona.get(pid))
        except Exception as exc:  # un punto malo no detiene el resto
            print(f'[{i}/{len(archivos)}] {pid}: ERROR {type(exc).__name__}: {exc}', flush=True)
            continue
        total += filas
        print(f'[{i}/{len(archivos)}] {pid}: {filas} filas ({time.monotonic() - t0:.1f} s)', flush=True)
    print(f'Listo: {total} filas nuevas en {salida}')


if __name__ == '__main__':
    main()
