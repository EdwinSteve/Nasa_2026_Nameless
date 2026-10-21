"""Serie diaria de un punto (JSON de datos_tierra) en arreglos NumPy.

Solo columnas corregidas: temperatura `derived_*_corr` (ADR 0002), lluvia `derived_precip_mm`
y ET0 `derived_et0_mm`. Nunca `power_t2m*` sin corregir.
"""
import gzip
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

COLUMNAS = {
    't': 'derived_t2m_corr',
    'tmax': 'derived_t2m_max_corr',
    'tmin': 'derived_t2m_min_corr',
    'lluvia': 'derived_precip_mm',
    'lluvia_power': 'power_prectotcorr',
    'hr': 'power_rh2m',
    'viento': 'power_ws2m',
    'radiacion': 'power_allsky_sfc_sw_dwn',
    'et0': 'derived_et0_mm',
    'sm_raiz': 'smap_sm_rootzone',
    'sm_superficie': 'smap_sm_surface',
    'imerg': 'imerg_precip_mm',
}
# Las que el oráculo necesita sin huecos (se rellenan con interpolación lineal)
CONTINUAS = ('t', 'tmax', 'tmin', 'lluvia', 'hr', 'viento', 'et0')


@dataclass
class Serie:
    id: str
    lat: float
    lon: float
    elevacion_m: float
    celda_power_m: float
    fechas: np.ndarray                     # datetime64[D]
    v: dict[str, np.ndarray]               # columnas de COLUMNAS, float64 con NaN
    suelo: dict | None
    enso: list[dict] = field(default_factory=list)

    @property
    def anios(self) -> np.ndarray:
        return self.fechas.astype('datetime64[Y]').astype(int) + 1970

    def indice(self, dia: date) -> int:
        return int((np.datetime64(dia, 'D') - self.fechas[0]).astype(int))


def _rellenar(x: np.ndarray) -> np.ndarray:
    """Interpola huecos aislados de POWER (−999 ya viene como None) para que el balance no se corte."""
    malos = ~np.isfinite(x)
    if not malos.any() or malos.all():
        return x
    idx = np.arange(len(x))
    x = x.copy()
    x[malos] = np.interp(idx[malos], idx[~malos], x[~malos])
    return x


def desde_json(datos: dict, punto_id: str | None = None) -> Serie:
    diario = datos['daily']
    v = {}
    for corto, columna in COLUMNAS.items():
        v[corto] = np.array([np.nan if f.get(columna) is None else f[columna] for f in diario], dtype=np.float64)
    for corto in CONTINUAS:
        v[corto] = _rellenar(v[corto])
    sitio = datos['site']
    return Serie(
        id=punto_id or sitio.get('point_id') or f"{datos['location']['lat']}_{datos['location']['lon']}",
        lat=datos['location']['lat'],
        lon=datos['location']['lon'],
        elevacion_m=np.nan if sitio.get('elevation_m') is None else sitio['elevation_m'],
        celda_power_m=np.nan if sitio.get('power_cell_elevation_m') is None else sitio['power_cell_elevation_m'],
        fechas=np.array([f['date'] for f in diario], dtype='datetime64[D]'),
        v=v,
        suelo=datos.get('soil') if datos.get('soil') and not datos['soil'].get('empty') else None,
        enso=datos.get('enso') or [],
    )


def cargar(ruta: Path) -> Serie:
    ruta = Path(ruta)
    abrir = gzip.open if ruta.suffix == '.gz' else open
    with abrir(ruta, 'rt', encoding='utf-8') as fh:
        datos = json.load(fh)
    return desde_json(datos, ruta.name.split('.')[0])
