"""
Lección 1 — NASA POWER
Consulta de series climáticas diarias para un punto, limpieza, control de calidad,
grados-día y procedencia del dato.

Uso:
    pip install requests pandas
    python leccion_01_nasa_power.py
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pandas as pd
import requests

URL_BASE = "https://power.larc.nasa.gov/api/temporal/daily/point"

PARAMETROS_SURCO = [
    "T2M", "T2M_MAX", "T2M_MIN",   # temperatura (°C)
    "PRECTOTCORR",                 # lluvia corregida (mm/día)
    "RH2M", "WS2M",                # humedad (%) y viento (m/s)
    "ALLSKY_SFC_SW_DWN",           # radiación (MJ/m²/día con community=AG)
]


# ---------------------------------------------------------------------------
# 1. Petición HTTP con tiempo límite y reintentos
# ---------------------------------------------------------------------------
def consultar_power(lat: float, lon: float, inicio: str, fin: str,
                    parametros: list[str] = PARAMETROS_SURCO,
                    comunidad: str = "AG", reintentos: int = 3) -> dict:
    """Devuelve el JSON crudo de POWER. inicio y fin en formato AAAAMMDD."""
    params = {
        "parameters": ",".join(parametros),
        "community": comunidad,
        "latitude": lat,
        "longitude": lon,
        "start": inicio,
        "end": fin,
        "format": "JSON",
    }
    for intento in range(1, reintentos + 1):
        try:
            r = requests.get(URL_BASE, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if intento == reintentos:
                raise
            espera = 2 ** intento          # espera creciente: 2, 4, 8 s
            print(f"Intento {intento} falló ({e}); reintento en {espera} s")
            time.sleep(espera)
    raise RuntimeError("No se pudo consultar POWER")


# ---------------------------------------------------------------------------
# 2. JSON -> tabla, con valores de relleno convertidos a NaN
# ---------------------------------------------------------------------------
def a_dataframe(crudo: dict) -> pd.DataFrame:
    datos = crudo["properties"]["parameter"]           # {VAR: {AAAAMMDD: valor}}
    relleno = crudo.get("header", {}).get("fill_value", -999.0)

    df = pd.DataFrame(datos)                            # filas = fechas, columnas = variables
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "fecha"
    df = df.sort_index().astype(float)
    df = df.mask(df == relleno)                         # -999 -> NaN
    return df


# ---------------------------------------------------------------------------
# 3. Control de calidad
# ---------------------------------------------------------------------------
def reporte_calidad(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "faltantes": df.isna().sum(),
        "pct_faltante": (df.isna().mean() * 100).round(2),
        "primer_dato": df.apply(lambda s: s.first_valid_index()),
        "ultimo_dato": df.apply(lambda s: s.last_valid_index()),
    })


# ---------------------------------------------------------------------------
# 4. Variable agronómica: grados-día de crecimiento
# ---------------------------------------------------------------------------
def calcular_gdd(df: pd.DataFrame, t_base: float = 10.0,
                 t_tope: float = 30.0) -> pd.Series:
    """GDD diario = max(0, (min(Tmax, tope) + max(Tmin, base)) / 2 - base)."""
    tmax = df["T2M_MAX"].clip(upper=t_tope)
    tmin = df["T2M_MIN"].clip(lower=t_base)
    gdd = ((tmax + tmin) / 2 - t_base).clip(lower=0)
    return gdd.rename("GDD")


# ---------------------------------------------------------------------------
# 5. Procedencia y caché por celda
# ---------------------------------------------------------------------------
def celda_power(lat: float, lon: float) -> tuple[float, float]:
    """Redondea a la grilla de MERRA-2 (0,5° lat x 0,625° lon) para usar como clave de caché."""
    return round(round(lat / 0.5) * 0.5, 3), round(round(lon / 0.625) * 0.625, 3)


def construir_procedencia(crudo: dict, lat: float, lon: float) -> dict:
    unidades = {k: v.get("units") for k, v in crudo.get("parameters", {}).items()}
    return {
        "fuente": "NASA POWER",
        "endpoint": URL_BASE,
        "fuentes_internas": crudo.get("header", {}).get("sources"),
        "punto_consultado": {"lat": lat, "lon": lon},
        "celda": celda_power(lat, lon),
        "unidades": unidades,
        "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ---------------------------------------------------------------------------
# Ejecución de ejemplo: Neiva, año 2024
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    LAT, LON = 2.93, -75.28

    crudo = consultar_power(LAT, LON, "20240101", "20241231")
    df = a_dataframe(crudo)

    print("\n== Calidad de los datos ==")
    print(reporte_calidad(df))

    df["GDD_maiz"] = calcular_gdd(df, t_base=10, t_tope=30)

    print("\n== Resumen mensual ==")
    mensual = df.resample("MS").agg({
        "T2M": "mean", "T2M_MAX": "max", "PRECTOTCORR": "sum", "GDD_maiz": "sum",
    }).round(1)
    print(mensual)

    print("\n== Procedencia ==")
    for k, v in construir_procedencia(crudo, LAT, LON).items():
        print(f"{k}: {v}")

    df.to_csv("power_neiva_2024.csv")
    print("\nGuardado en power_neiva_2024.csv")
