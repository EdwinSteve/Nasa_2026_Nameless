"""Valida la calidad de los datos de un punto descargándolos de la web.

Qué hace:
  1. Elevación real del punto (Copernicus DEM 90 m vía Open-Meteo).
  2. NASA POWER diario: completitud, rangos físicos y coherencia (Tmin <= T <= Tmax).
  3. Corrección de temperatura por elevación (ADR 0002): compara POWER crudo y
     corregido contra una referencia independiente (reanálisis ERA5 de Open-Meteo,
     ajustado a la elevación real).
  4. Precipitación mensual POWER vs referencia.
  5. SoilGrids: que haya datos y que sean físicamente plausibles.

Solo usa la biblioteca estándar.

    python scripts/validar_datos.py                              # punto rural al norte de Neiva
    python scripts/validar_datos.py --lat 2.69 --lon -75.33 --nombre campoalegre
"""

import argparse
import json
import math
import pathlib
import statistics as st
import urllib.parse
import urllib.request
from collections import defaultdict

RAIZ = pathlib.Path(__file__).resolve().parent.parent
LAPSE = 0.0065  # °C por metro

RANGOS_POWER = {  # límites físicos razonables para el trópico andino
    "T2M": (0, 45), "T2M_MAX": (0, 50), "T2M_MIN": (-5, 40),
    "PRECTOTCORR": (0, 300), "RH2M": (0, 100), "ALLSKY_SFC_SW_DWN": (0, 40),
    "GWETROOT": (0, 1), "GWETTOP": (0, 1),
}


def get(url, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "nasa2026-nameless/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def elevacion(lat, lon):
    return get(f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}")["elevation"][0]


def power(lat, lon, inicio, fin):
    d = get("https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters={','.join(RANGOS_POWER)}&community=AG"
            f"&latitude={lat}&longitude={lon}&start={inicio}0101&end={fin}1231&format=JSON")
    fill = d["header"]["fill_value"]
    p = d["properties"]["parameter"]
    serie = {k: {f"{f[:4]}-{f[4:6]}-{f[6:]}": (None if v == fill else v) for f, v in p[k].items()} for k in p}
    return serie, d["geometry"]["coordinates"][2]


def referencia(lat, lon, inicio, fin):
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "start_date": f"{inicio}-01-01", "end_date": f"{fin}-12-31",
        "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "America/Bogota"})
    d = get(f"https://archive-api.open-meteo.com/v1/archive?{q}")["daily"]
    return {k: dict(zip(d["time"], d[k])) for k in d if k != "time"}


def soilgrids(lat, lon):
    q = urllib.parse.urlencode(
        [("lon", lon), ("lat", lat)]
        + [("property", p) for p in ("phh2o", "clay", "sand", "silt", "soc", "nitrogen", "bdod")]
        + [("depth", "0-5cm"), ("depth", "15-30cm"), ("depth", "30-60cm"), ("value", "mean")])
    d = get(f"https://rest.isric.org/soilgrids/v2.0/properties/query?{q}")
    out = {}
    for layer in d["properties"]["layers"]:
        f = layer["unit_measure"]["d_factor"]
        for dep in layer["depths"]:
            v = dep["values"]["mean"]
            out.setdefault(dep["label"], {})[layer["name"]] = None if v is None else v / f
    return out


def comparar(a, b):
    """Sesgo, RMSE y correlación entre dos series {fecha: valor}."""
    pares = [(a[k], b[k]) for k in a if k in b and a[k] is not None and b[k] is not None]
    x, y = zip(*pares)
    dif = [i - j for i, j in pares]
    return {"n": len(pares), "sesgo": round(st.mean(dif), 2),
            "rmse": round(math.sqrt(st.mean(d * d for d in dif)), 2),
            "r": round(st.correlation(x, y), 3)}


def por_mes(serie, agg):
    grupos = defaultdict(list)
    for f, v in serie.items():
        if v is not None:
            grupos[f[:7]].append(v)
    return {m: agg(v) for m, v in grupos.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, default=3.02)
    ap.add_argument("--lon", type=float, default=-75.25)
    ap.add_argument("--nombre", default="neiva-norte")
    ap.add_argument("--inicio", type=int, default=2015)
    ap.add_argument("--fin", type=int, default=2024)
    a = ap.parse_args()

    checks = []  # (estado, descripción)

    def check(ok, texto, aviso=False):
        checks.append(("✅" if ok else ("⚠️" if aviso else "❌"), texto))

    print("Descargando elevación, POWER, referencia ERA5 y SoilGrids...", flush=True)
    elev = elevacion(a.lat, a.lon)
    pw, elev_celda = power(a.lat, a.lon, a.inicio, a.fin)
    ref = referencia(a.lat, a.lon, a.inicio, a.fin)
    suelo = soilgrids(a.lat, a.lon)
    delta = (elev_celda - elev) * LAPSE

    # 1. Completitud y rangos
    n_dias = len(pw["T2M"])
    esperado = sum(366 if y % 4 == 0 else 365 for y in range(a.inicio, a.fin + 1))
    check(n_dias == esperado, f"POWER entrega {n_dias} de {esperado} días esperados")
    completitud = {}
    for k, (lo, hi) in RANGOS_POWER.items():
        vals = [v for v in pw[k].values() if v is not None]
        faltan = n_dias - len(vals)
        fuera = [v for v in vals if not lo <= v <= hi]
        completitud[k] = {"faltantes": faltan, "fuera_de_rango": len(fuera),
                          "min": min(vals), "max": max(vals), "media": round(st.mean(vals), 2)}
        check(faltan == 0 and not fuera,
              f"{k}: {faltan} faltantes, {len(fuera)} fuera de [{lo}, {hi}] (min {min(vals)}, max {max(vals)})",
              aviso=faltan < n_dias * 0.01 and not fuera)
    incoh = sum(1 for f in pw["T2M"]
                if None not in (pw["T2M_MIN"][f], pw["T2M"][f], pw["T2M_MAX"][f])
                and not pw["T2M_MIN"][f] <= pw["T2M"][f] <= pw["T2M_MAX"][f])
    check(incoh == 0, f"Coherencia Tmin ≤ T ≤ Tmax: {incoh} días incoherentes")

    # 2. Temperatura: POWER crudo vs corregido vs referencia
    t_crudo = pw["T2M"]
    t_corr = {f: (None if v is None else v + delta) for f, v in t_crudo.items()}
    c_crudo = comparar(t_crudo, ref["temperature_2m_mean"])
    c_corr = comparar(t_corr, ref["temperature_2m_mean"])
    tmax_corr = {f: (None if v is None else v + delta) for f, v in pw["T2M_MAX"].items()}
    c_tmax = comparar(tmax_corr, ref["temperature_2m_max"])
    check(abs(c_corr["sesgo"]) < 1.5,
          f"Temperatura media corregida vs referencia: sesgo {c_corr['sesgo']} °C "
          f"(sin corregir: {c_crudo['sesgo']} °C)", aviso=abs(c_corr["sesgo"]) < 3)
    check(c_corr["r"] > 0.6, f"Correlación diaria de temperatura: r = {c_corr['r']}", aviso=c_corr["r"] > 0.4)

    # 3. Precipitación mensual
    p_pw = por_mes(pw["PRECTOTCORR"], sum)
    p_ref = por_mes(ref["precipitation_sum"], sum)
    c_prec = comparar(p_pw, p_ref)
    anual_pw = sum(p_pw.values()) / (a.fin - a.inicio + 1)
    anual_ref = sum(p_ref.values()) / (a.fin - a.inicio + 1)
    check(c_prec["r"] > 0.6, f"Precipitación mensual POWER vs referencia: r = {c_prec['r']}, "
          f"anual {anual_pw:.0f} vs {anual_ref:.0f} mm", aviso=c_prec["r"] > 0.4)

    # Climatología mensual (ciclo bimodal esperado en el Huila)
    clim = {}
    for m in range(1, 13):
        mm = f"{m:02d}"
        pm = [v for k, v in p_pw.items() if k[5:] == mm]
        pr = [v for k, v in p_ref.items() if k[5:] == mm]
        tm = [v for f, v in t_corr.items() if f[5:7] == mm and v is not None]
        clim[mm] = {"T_corr": round(st.mean(tm), 1), "P_power": round(st.mean(pm)), "P_ref": round(st.mean(pr))}

    # 4. GDD base 10 °C con POWER corregido
    gdd = {}
    for f in pw["T2M_MAX"]:
        tx, tn = pw["T2M_MAX"][f], pw["T2M_MIN"][f]
        if tx is not None and tn is not None:
            gdd.setdefault(f[:4], 0)
            gdd[f[:4]] += max(0, (tx + tn) / 2 + delta - 10)
    gdd = {y: round(v) for y, v in gdd.items()}

    # 5. Suelo
    sup = suelo.get("0-5cm", {})
    hay_suelo = any(v is not None for v in sup.values())
    check(hay_suelo, "SoilGrids devuelve datos para el punto")
    if hay_suelo:
        textura = sum(sup[k] for k in ("clay", "sand", "silt"))
        check(95 <= textura <= 105, f"Textura arcilla+arena+limo = {textura:.1f} %")
        check(4 <= sup["phh2o"] <= 8.5, f"pH {sup['phh2o']} en rango agrícola")

    # Reporte
    res = {"punto": {"nombre": a.nombre, "lat": a.lat, "lon": a.lon, "elev_dem_m": elev,
                     "elev_celda_power_m": round(elev_celda), "correccion_C": round(delta, 2)},
           "periodo": [a.inicio, a.fin], "completitud_power": completitud,
           "temperatura": {"crudo_vs_ref": c_crudo, "corregido_vs_ref": c_corr, "tmax_corregido_vs_ref": c_tmax},
           "precipitacion_mensual": {**c_prec, "anual_power_mm": round(anual_pw), "anual_ref_mm": round(anual_ref)},
           "climatologia": clim, "gdd_base10_por_anio": gdd, "suelo": suelo,
           "checks": [{"estado": e, "check": t} for e, t in checks]}
    out = RAIZ / f"data/processed/validacion_{a.nombre}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nPunto {a.nombre} ({a.lat}, {a.lon}) · DEM {elev:.0f} m · celda POWER {elev_celda:.0f} m "
          f"· corrección +{delta:.2f} °C · {a.inicio}-{a.fin}\n")
    for e, t in checks:
        print(f"{e} {t}")
    print("\nMes  T_corr  P_POWER  P_ref (mm)")
    for m, v in clim.items():
        print(f" {m}   {v['T_corr']:5}  {v['P_power']:6}  {v['P_ref']:6}")
    print(f"\nGDD base 10 °C por año: {gdd}")
    print(f"Suelo 0-5 cm: {sup}")
    print(f"\nResultado completo: {out.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
