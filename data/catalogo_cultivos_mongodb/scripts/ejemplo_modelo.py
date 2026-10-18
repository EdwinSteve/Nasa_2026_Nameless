"""
Ejemplo: cómo el modelo predictivo usa el catálogo para calificar las condiciones
de una fase con la serie diaria de NASA POWER.

Uso:
    python scripts/ejemplo_modelo.py                     # lee datos/cultivos.json
    SURCO_MONGO_URI=mongodb://localhost:27017 python scripts/ejemplo_modelo.py   # lee de MongoDB
"""
from __future__ import annotations
import json, os, random
from statistics import mean


def cargar_cultivo(cultivo_id: str) -> dict:
    uri = os.getenv("SURCO_MONGO_URI")
    if uri:
        from pymongo import MongoClient
        return MongoClient(uri)["surco_agro"]["cultivos"].find_one({"_id": cultivo_id})
    ruta = os.path.join(os.path.dirname(__file__), "..", "datos", "cultivos.json")
    return next(c for c in json.load(open(ruta, encoding="utf-8")) if c["_id"] == cultivo_id)


def trapecio(x: float, t: dict) -> float:
    """Pertenencia 0-1 a un trapecio {min_absoluto, optimo_min, optimo_max, max_absoluto}."""
    a, b, c, d = t["min_absoluto"], t["optimo_min"], t["optimo_max"], t["max_absoluto"]
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    return (x - a) / (b - a) if x < b else (d - x) / (d - c)


def rango(x: float, r: dict, margen: float = 20.0) -> float:
    """1 dentro del rango óptimo; decae linealmente hasta 0 a 'margen' unidades de distancia."""
    if r["optimo_min"] <= x <= r["optimo_max"]:
        return 1.0
    dist = r["optimo_min"] - x if x < r["optimo_min"] else x - r["optimo_max"]
    return max(0.0, 1 - dist / margen)


def evaluar_fase(fase: dict, serie: list[dict], riego_mm: float = 0.0) -> dict:
    """serie: lista de días con T2M, T2M_MAX, PRECTOTCORR, RH2M y WS2M (NASA POWER)."""
    t_media = mean(d["T2M"] for d in serie)
    lluvia = sum(d["PRECTOTCORR"] for d in serie) + riego_mm
    puntajes = {
        "temperatura": trapecio(t_media, fase["temperatura_aire_C"]),
        "agua": trapecio(lluvia, fase["precipitacion_mm"]),
        "humedad_relativa": rango(mean(d["RH2M"] for d in serie), fase["humedad_relativa_pct"]),
        "viento": 1 - sum(d["WS2M"] > fase["viento_2m_ms"]["max_tolerable"] for d in serie) / len(serie),
    }
    if fase.get("temp_max_critica_C"):
        dias_calor = sum(d["T2M_MAX"] > fase["temp_max_critica_C"] for d in serie)
        puntajes["calor_critico"] = max(0.0, 1 - dias_calor / 5)  # 5 días o más sobre la crítica = 0
    puntajes["fase"] = round(min(puntajes.values()) * 0.5 + mean(puntajes.values()) * 0.5, 3)
    puntajes["detalle"] = {"t_media_C": round(t_media, 1), "lluvia_mm": round(lluvia, 1)}
    return puntajes


def serie_sintetica(dias: int, semilla: int = 7) -> list[dict]:
    """Serie de prueba parecida al valle de Neiva (reemplazar por datos reales de POWER)."""
    rnd = random.Random(semilla)
    return [{"T2M": rnd.gauss(27.5, 1.0), "T2M_MAX": rnd.gauss(33.5, 1.5),
             "PRECTOTCORR": max(0.0, rnd.gauss(4.0, 4.0)), "RH2M": rnd.gauss(66, 5),
             "WS2M": abs(rnd.gauss(2.0, 0.8))} for _ in range(dias)]


if __name__ == "__main__":
    maiz = cargar_cultivo("maiz")
    print(f"Cultivo: {maiz['nombre']}")
    for fase in maiz["fases"]:
        dias = round((fase["duracion_dias"]["min"] + fase["duracion_dias"]["max"]) / 2)
        r = evaluar_fase(fase, serie_sintetica(dias, semilla=fase["orden"]))
        print(f"  {fase['nombre']:<32} {dias:>3} días  puntaje={r['fase']:.2f}  "
              f"T={r['detalle']['t_media_C']} °C  lluvia={r['detalle']['lluvia_mm']} mm")
    veg = next(f for f in maiz["fases"] if f["codigo"] == "vegetativo")
    flo = next(f for f in maiz["fases"] if f["codigo"] == "floracion")
    m_crec = evaluar_fase(veg, serie_sintetica(38, 2))["fase"]
    m_flor = evaluar_fase(flo, serie_sintetica(21, 3))["fase"]
    print(f"\nComponentes del índice IP:  M_crecimiento={m_crec:.2f}  M_floracion={m_flor:.2f}")
