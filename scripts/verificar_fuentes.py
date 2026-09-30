"""Verifica que las fuentes de datos del proyecto respondan para un punto y una zona.

Solo usa la biblioteca estándar: no requiere login ni dependencias.

    python scripts/verificar_fuentes.py                       # punto por defecto (zona arrocera de Campoalegre, Huila)
    python scripts/verificar_fuentes.py --lat 2.93 --lon -75.28
    python scripts/verificar_fuentes.py --json data/processed/verificacion.json
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

POWER = "https://power.larc.nasa.gov/api"
SOILGRIDS = "https://rest.isric.org/soilgrids/v2.0/properties/query"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"

# (short_name, version, para qué lo usamos)
COLECCIONES = [
    ("SPL3SMP_E", "006", "SMAP humedad superficial 9 km diaria"),
    ("SPL4SMGP", "008", "SMAP L4 humedad superficie + zona radicular 9 km, 3 h"),
    ("GPM_3IMERGDF", "07", "IMERG Final diario (latencia ~3.5 meses)"),
    ("GPM_3IMERGDL", "07", "IMERG Late diario (casi tiempo real)"),
    ("MOD13Q1", "061", "MODIS NDVI/EVI 250 m, 16 días"),
    ("MOD11A2", "061", "MODIS LST 1 km, 8 días"),
    ("MOD16A2GF", "061", "MODIS ET 500 m, 8 días (gap-filled)"),
    ("HLSL30", "2.0", "HLS Landsat 30 m"),
    ("HLSS30", "2.0", "HLS Sentinel-2 30 m"),
    ("ECO_L4T_ESI", "002", "ECOSTRESS índice de estrés evaporativo ~70 m"),
    ("ECO_L3T_JET", "002", "ECOSTRESS evapotranspiración ~70 m"),
    ("MCD12Q1", "061", "MODIS cobertura del suelo anual 500 m"),
]


def get(url, timeout=90, headers=False):
    req = urllib.request.Request(url, headers={"User-Agent": "nasa2026-nameless/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return (json.loads(body), dict(r.headers)) if headers else json.loads(body)


def check_power(lat, lon, elev_real):
    params = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR"
    d = get(f"{POWER}/temporal/climatology/point?parameters={params}"
            f"&community=AG&latitude={lat}&longitude={lon}&format=JSON")
    elev_celda = d["geometry"]["coordinates"][2]
    p = d["properties"]["parameter"]
    t2m = p["T2M"]["ANN"]
    out = {
        "elevacion_celda_m": round(elev_celda),
        "T2M_anual_C": t2m,
        "precip_anual_mm": round(p["PRECTOTCORR"]["ANN"] * 365),
    }
    if elev_real is not None:
        # Gradiente térmico estándar: -6.5 °C por km
        out["T2M_corregida_C"] = round(t2m + (elev_celda - elev_real) * 0.0065, 1)
    return out


def check_soilgrids(lat, lon):
    q = urllib.parse.urlencode(
        [("lon", lon), ("lat", lat)]
        + [("property", p) for p in ("phh2o", "clay", "sand", "soc", "nitrogen")]
        + [("depth", "0-5cm"), ("depth", "15-30cm"), ("value", "mean")])
    d = get(f"{SOILGRIDS}?{q}")
    out = {}
    for layer in d["properties"]["layers"]:
        factor = layer["unit_measure"]["d_factor"]
        for depth in layer["depths"]:
            v = depth["values"]["mean"]
            out[f"{layer['name']}_{depth['label']}"] = None if v is None else v / factor
    if all(v is None for v in out.values()):
        out["aviso"] = "sin datos (probablemente zona urbana o agua): usar un punto rural"
    return out


def check_cmr(bbox, year):
    out = {}
    temporal = f"{year}-01-01T00:00:00Z,{year}-12-31T23:59:59Z"
    for short, ver, desc in COLECCIONES:
        base = f"{CMR}?short_name={short}&version={ver}&bounding_box={bbox}"
        _, h = get(f"{base}&temporal={temporal}&page_size=0", headers=True)
        hits = int({k.lower(): v for k, v in h.items()}["cmr-hits"])
        last = get(f"{base}&sort_key=-start_date&page_size=1")["feed"]["entry"]
        out[short] = {
            "descripcion": desc,
            f"granulos_{year}": hits,
            "ultimo": last[0]["time_start"][:10] if last else None,
        }
        time.sleep(0.2)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, default=2.69)
    ap.add_argument("--lon", type=float, default=-75.33)
    ap.add_argument("--elev", type=float, default=525, help="elevación real del punto en m (para corregir POWER)")
    ap.add_argument("--bbox", default="-76.6,1.5,-74.4,3.9", help="W,S,E,N (por defecto: Huila)")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--json", help="guardar el resultado en este archivo")
    a = ap.parse_args()

    res = {"punto": {"lat": a.lat, "lon": a.lon, "elev_m": a.elev}, "bbox": a.bbox}
    for name, fn in [("power", lambda: check_power(a.lat, a.lon, a.elev)),
                     ("soilgrids", lambda: check_soilgrids(a.lat, a.lon)),
                     ("cmr", lambda: check_cmr(a.bbox, a.year))]:
        try:
            res[name] = fn()
        except Exception as e:  # una fuente caída no debe tumbar el resto del reporte
            res[name] = {"error": str(e)}
        print(f"== {name}\n{json.dumps(res[name], indent=2, ensure_ascii=False)}", flush=True)

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
