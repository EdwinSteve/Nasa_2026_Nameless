"""Descarga series diarias de NASA POWER para las fincas demo y las guarda en CSV.

    python scripts/descargar_power.py                    # 2015-2024, todas las fincas
    python scripts/descargar_power.py --inicio 2020 --fin 2024

Salida: data/raw/power/<id>.csv (data/raw no se versiona). Agrega la columna
T2M_corr: temperatura corregida por la diferencia entre la elevación de la
celda POWER (~50 km) y la elevación real del punto (-6.5 °C/km).
"""

import argparse
import csv
import json
import pathlib
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN",
          "GWETROOT", "GWETTOP", "EVPTRNS", "WS2M"]
LAPSE = 0.0065  # °C por metro


def descargar(finca, inicio, fin):
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point"
           f"?parameters={','.join(PARAMS)}&community=AG"
           f"&latitude={finca['lat']}&longitude={finca['lon']}"
           f"&start={inicio}0101&end={fin}1231&format=JSON")
    with urllib.request.urlopen(url, timeout=300) as r:
        d = json.load(r)
    fill = d["header"]["fill_value"]
    delta = (d["geometry"]["coordinates"][2] - finca["elev_m"]) * LAPSE
    p = d["properties"]["parameter"]
    fechas = sorted(p["T2M"])
    filas = []
    for f in fechas:
        fila = {"fecha": f"{f[:4]}-{f[4:6]}-{f[6:]}"}
        for k in PARAMS:
            v = p[k][f]
            fila[k] = "" if v == fill else v
        for k in ("T2M", "T2M_MAX", "T2M_MIN"):
            fila[f"{k}_corr"] = "" if fila[k] == "" else round(fila[k] + delta, 2)
        filas.append(fila)
    return filas, d["geometry"]["coordinates"][2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", type=int, default=2015)
    ap.add_argument("--fin", type=int, default=2024)
    a = ap.parse_args()
    fincas = json.loads((RAIZ / "data/fincas_demo.json").read_text(encoding="utf-8"))["fincas"]
    salida = RAIZ / "data/raw/power"
    salida.mkdir(parents=True, exist_ok=True)
    for finca in fincas:
        filas, elev_celda = descargar(finca, a.inicio, a.fin)
        ruta = salida / f"{finca['id']}.csv"
        with ruta.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)
        print(f"{finca['id']}: {len(filas)} días, celda a {elev_celda:.0f} m vs punto a {finca['elev_m']} m -> {ruta.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
