"""Catálogo surco_agro en arreglos para el oráculo (Numba) y como features del cultivo.

Lee el mismo JSON que se carga en Mongo, así el entrenamiento no necesita la base.
"""
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .rutas import CATALOGO

MAX_FASES = 6
TIPOS_CICLO = ('transitorio', 'semiperenne', 'perenne')
# Cultivos que por definición se riegan: el oráculo no los puntúa contra la lluvia (el agua
# está asegurada) y la etiqueta riego_mm mide cuánta hace falta.
CON_RIEGO = {'arroz_riego'}
TOLERANCIA = {'baja': 0, 'media': 1, 'alta': 2}


def cargar(ruta: Path = CATALOGO) -> list[dict]:
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


def _num(valor) -> float:
    return np.nan if valor is None else float(valor)


def _trapecio(t: dict | None) -> list[float]:
    t = t or {}
    return [_num(t.get(k)) for k in ('min_absoluto', 'optimo_min', 'optimo_max', 'max_absoluto')]


def duracion_fase(fase: dict) -> int:
    """Días de la fase: punto medio del rango del catálogo."""
    d = fase['duracion_dias']
    return int(round((d['min'] + d['max']) / 2))


@dataclass
class Cultivos:
    """Fases de todos los cultivos en arreglos rellenos hasta MAX_FASES (NaN o 0 donde no hay fase)."""
    ids: list[str]
    version: list[int]
    n_fases: np.ndarray        # (C,)
    duracion: np.ndarray       # (C, F) días
    fraccion: np.ndarray       # (C, F) peso de la fase en el puntaje
    kc: np.ndarray             # (C, F)
    p: np.ndarray              # (C, F)
    temp: np.ndarray           # (C, F, 4) trapecio de temperatura media
    lluvia: np.ndarray         # (C, F, 4) trapecio de lluvia acumulada en la fase (mm)
    hr: np.ndarray             # (C, F, 2) rango óptimo de humedad relativa
    viento_max: np.ndarray     # (C, F) viento máximo tolerable
    temp_critica: np.ndarray   # (C, F) temperatura máxima crítica (NaN si la fase no tiene)
    zr: np.ndarray             # (C,) profundidad de raíz (m)
    tiene_agua: np.ndarray     # (C,) True si hay Kc y p para el balance hídrico
    con_riego: np.ndarray      # (C,) True si el sistema es con riego (CON_RIEGO)

    @property
    def dias_ciclo(self) -> np.ndarray:
        return self.duracion.sum(axis=1)


def a_arreglos(cultivos: list[dict]) -> Cultivos:
    c = len(cultivos)
    forma = (c, MAX_FASES)
    out = dict(
        n_fases=np.zeros(c, np.int64), duracion=np.zeros(forma, np.int64), fraccion=np.zeros(forma),
        kc=np.full(forma, np.nan), p=np.full(forma, np.nan), temp=np.full(forma + (4,), np.nan),
        lluvia=np.full(forma + (4,), np.nan), hr=np.full(forma + (2,), np.nan),
        viento_max=np.full(forma, np.nan), temp_critica=np.full(forma, np.nan),
        zr=np.full(c, np.nan), tiene_agua=np.zeros(c, bool),
        con_riego=np.array([x['_id'] in CON_RIEGO for x in cultivos]),
    )
    for i, cultivo in enumerate(cultivos):
        fases = sorted(cultivo['fases'], key=lambda f: f['orden'])
        assert len(fases) <= MAX_FASES, cultivo['_id']
        suelo = cultivo['requerimientos_cultivo']['suelo']
        out['n_fases'][i] = len(fases)
        out['zr'][i] = _num(suelo.get('profundidad_raiz_m'))
        for j, f in enumerate(fases):
            out['duracion'][i, j] = duracion_fase(f)
            out['fraccion'][i, j] = f['fraccion_del_ciclo']
            out['kc'][i, j] = _num(f.get('kc'))
            out['p'][i, j] = _num(f.get('agotamiento_permitido_p', suelo.get('agotamiento_permitido_p')))
            out['temp'][i, j] = _trapecio(f['temperatura_aire_C'])
            out['lluvia'][i, j] = _trapecio(f['precipitacion_mm'])
            out['hr'][i, j] = [_num(f['humedad_relativa_pct'].get(k)) for k in ('optimo_min', 'optimo_max')]
            out['viento_max'][i, j] = _num(f['viento_2m_ms'].get('max_tolerable'))
            out['temp_critica'][i, j] = _num(f.get('temp_max_critica_C'))
        n = len(fases)
        out['tiene_agua'][i] = bool(
            np.isfinite(out['zr'][i]) and np.isfinite(out['kc'][i, :n]).all() and np.isfinite(out['p'][i, :n]).all()
        )
    return Cultivos(ids=[x['_id'] for x in cultivos], version=[x['version'] for x in cultivos], **out)


def features(cultivos: list[dict]) -> dict[str, np.ndarray]:
    """Ficha del cultivo como columnas (sección 3: 'Cultivo'). Una fila por cultivo."""
    familias = sorted({x['familia'] for x in cultivos})
    grupos = sorted({x['grupo'] for x in cultivos})
    filas = []
    for x in cultivos:
        r = x['requerimientos_cultivo']
        s = r['suelo']
        kc = r.get('kc') or {}
        fases = x['fases']
        criticas = [f['temp_max_critica_C'] for f in fases if f.get('temp_max_critica_C') is not None]
        fila = {
            'c_tipo_ciclo': TIPOS_CICLO.index(x['tipo_ciclo']),
            'c_con_riego': float(x['_id'] in CON_RIEGO),
            'c_grupo': grupos.index(x['grupo']),
            'c_familia': familias.index(x['familia']),
            'c_dias_ciclo': sum(duracion_fase(f) for f in fases),
            'c_n_fases': len(fases),
            'c_t_base': _num(r.get('t_base_C')),
            'c_temp_critica': max(criticas) if criticas else np.nan,
            'c_kc_ini': _num(kc.get('ini')), 'c_kc_mid': _num(kc.get('mid')), 'c_kc_end': _num(kc.get('end')),
            'c_zr': _num(s.get('profundidad_raiz_m')),
            'c_p': _num(s.get('agotamiento_permitido_p')),
            'c_tol_sequia': TOLERANCIA.get(s.get('tolerancia_sequia'), np.nan),
            'c_tol_encharcamiento': TOLERANCIA.get(s.get('tolerancia_encharcamiento'), np.nan),
            'c_hr_min': _num(r['humedad_relativa_pct'].get('optimo_min')),
            'c_hr_max': _num(r['humedad_relativa_pct'].get('optimo_max')),
            'c_viento_max': _num(r['viento_2m_ms'].get('max_tolerable')),
            'c_altitud_min': _num(x['zona_produccion']['altitud_msnm'].get('min')),
            'c_altitud_max': _num(x['zona_produccion']['altitud_msnm'].get('max')),
        }
        for nombre, t in (('temp', r['temperatura_aire_C']), ('agua', r['agua']), ('ph', s['ph']), ('n', s['N_O_CUL'])):
            for k, v in zip(('min_abs', 'opt_min', 'opt_max', 'max_abs'), _trapecio(t)):
                fila[f'c_{nombre}_{k}'] = v
        filas.append(fila)
    return {k: np.array([f[k] for f in filas], dtype=np.float32) for k in filas[0]}
