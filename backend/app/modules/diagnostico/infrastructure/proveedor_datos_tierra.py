"""Proveedor de datos del diagnóstico sobre el servicio datos_tierra (ml/datos_tierra).

Cada paso consulta solo su fuente, para que un dato lento (SoilGrids) o sin
credenciales (Earth Engine) no frene a los demás.
"""
import asyncio
import os
from datetime import date, timedelta
from statistics import mean
from types import SimpleNamespace

import httpx

from app.modules.diagnostico.domain import resumenes
from app.modules.diagnostico.domain.entity import LoteDiagnostico, ResultadoPaso

TIMEOUT = httpx.Timeout(180, connect=20)
DIAS_HUMEDAD = 30
DIAS_VERDOR = 120
BUFFER_SMAP_M = 5000   # una celda SMAP mide 9 km: un lote cabe dentro de un solo píxel
BUFFER_MODIS_M = 500   # unos cuatro píxeles MODIS de 250 m alrededor del lote
# El diagnóstico solo resume la capa arable: pedir menos hace que SoilGrids responda en segundos.
SUELO_PROPIEDADES = ["sand", "silt", "clay", "soc", "phh2o", "nitrogen", "wv0033", "wv1500"]
SUELO_PROFUNDIDADES = ["0-5cm", "5-15cm", "15-30cm"]


class DatosTierraNoInstalado(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Falta instalar el servicio de datos: pip install -e ../ml[gee]")


def _dt() -> SimpleNamespace:
    """Importa datos_tierra al usarlo: sin el paquete, la API arranca y el paso falla con un mensaje claro."""
    try:
        from datos_tierra import derivadas, suelo
        from datos_tierra.fuentes import dem, modis, power, smap, soilgrids
    except ImportError as exc:
        raise DatosTierraNoInstalado() from exc
    return SimpleNamespace(derivadas=derivadas, suelo=suelo, dem=dem, modis=modis, power=power, smap=smap,
                           soilgrids=soilgrids)


class ProveedorDatosTierra:
    def __init__(self, gee_project: str | None = None) -> None:
        # datos_tierra lee el proyecto de Earth Engine de la variable de entorno
        if gee_project:
            os.environ.setdefault("GEE_PROJECT", gee_project)

    async def clima(self, lote: LoteDiagnostico) -> ResultadoPaso:
        dt = _dt()
        fin = date(date.today().year - 1, 12, 31)   # solo años completos
        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            crudo, alturas = await asyncio.gather(
                dt.power.descargar(cliente, lote.lat, lote.lon, dt.power.INICIO, fin),
                dt.dem.elevaciones(cliente, [(lote.lat, lote.lon)]),
                return_exceptions=True,
            )
        if isinstance(crudo, BaseException):
            raise crudo
        series, meta = dt.power.series(crudo)
        elevacion = None if isinstance(alturas, BaseException) else alturas[0]
        correccion = (
            dt.derivadas.correccion_temperatura_c(meta["cell_elevation_m"], elevacion) if elevacion is not None else 0.0
        )

        temperaturas = [t + correccion for t in series["T2M"].values() if t is not None]
        maximas = [t + correccion for t in series["T2M_MAX"].values() if t is not None]
        por_anio: dict[int, list[float]] = {}
        for fecha, lluvia in series["PRECTOTCORR"].items():
            if lluvia is not None:
                por_anio.setdefault(int(fecha[:4]), []).append(lluvia)
        anuales = [sum(v) for v in por_anio.values() if len(v) >= 360]  # años casi completos
        if not temperaturas or not anuales:
            raise ValueError("NASA POWER no devolvió una serie suficiente para este punto.")

        lluvia_anual, t_media = mean(anuales), mean(temperaturas)
        anio_inicio, anio_fin = min(por_anio), max(por_anio)
        return ResultadoPaso(
            resumen=resumenes.resumen_clima(lluvia_anual, t_media, anio_inicio, anio_fin),
            datos={
                "lluvia_anual_mm": round(lluvia_anual, 1),
                "t_media_c": round(t_media, 2),
                "t_max_media_c": round(mean(maximas), 2),
                "anios": [anio_inicio, anio_fin],
                "elevacion_m": elevacion,
                "elevacion_celda_power_m": meta["cell_elevation_m"],
                "correccion_temperatura_c": round(correccion, 2),
                "fuente": "NASA POWER (AG) + SRTM 30 m, corrección ADR 0002",
            },
        )

    async def humedad(self, lote: LoteDiagnostico) -> ResultadoPaso:
        dt = _dt()
        fin = date.today()
        r = await asyncio.to_thread(
            dt.smap.descargar, lote.lat, lote.lon, fin - timedelta(days=DIAS_HUMEDAD + 10), fin, None, BUFFER_SMAP_M
        )
        valores = [f for f in r["series"] if f.get("sm_rootzone") is not None][-DIAS_HUMEDAD:]
        if not valores:
            raise ValueError("SMAP no tiene datos recientes para este punto.")
        theta = mean(f["sm_rootzone"] for f in valores)
        return ResultadoPaso(
            resumen=resumenes.resumen_humedad(theta, len(valores)),
            datos={
                "sm_rootzone_m3_m3": round(theta, 4),
                "sm_surface_m3_m3": valores[-1].get("sm_surface"),
                "ultimo_dia": valores[-1]["date"],
                "dias": len(valores),
                "fuente": r.get("collection"),
            },
        )

    async def suelo(self, lote: LoteDiagnostico) -> ResultadoPaso:
        dt = _dt()
        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            crudo = await dt.soilgrids.descargar(
                cliente, lote.lat, lote.lon,
                propiedades=SUELO_PROPIEDADES, profundidades=SUELO_PROFUNDIDADES, estadisticas=["mean"], por_consulta=4,
            )
        procesado = dt.suelo.procesar(crudo)
        if procesado["empty"]:
            raise ValueError("SoilGrids no tiene datos en este punto (zona urbana o cuerpo de agua).")
        capa = procesado["summary"]["0-30cm"]
        arena, limo, arcilla = (capa[p]["mean"] for p in ("sand", "silt", "clay"))
        if None in (arena, limo, arcilla):
            raise ValueError("SoilGrids no tiene la textura de este punto.")
        ph, mo = capa["phh2o"]["mean"], capa["organic_matter_pct"]
        return ResultadoPaso(
            resumen=resumenes.resumen_suelo(arena, limo, arcilla, ph, mo),
            datos={
                "textura": resumenes.textura_usda(arena, limo, arcilla),
                "arena_pct": arena,
                "limo_pct": limo,
                "arcilla_pct": arcilla,
                "ph": ph,
                "materia_organica_pct": mo,
                "nitrogeno_g_kg": capa["nitrogen"]["mean"],
                "theta_33_m3_m3": capa.get("wv0033", {}).get("mean"),
                "theta_1500_m3_m3": capa.get("wv1500", {}).get("mean"),
                "profundidad": "0-30 cm",
                "fuente": "ISRIC SoilGrids 2.0, media ponderada",
            },
        )

    async def verdor(self, lote: LoteDiagnostico) -> ResultadoPaso:
        dt = _dt()
        fin = date.today()
        r = await asyncio.to_thread(
            dt.modis.descargar, lote.lat, lote.lon, fin - timedelta(days=DIAS_VERDOR), fin, None, BUFFER_MODIS_M
        )
        validos = [f for f in r["ndvi"] if f.get("ndvi") is not None]
        if not validos:
            raise ValueError("Las imágenes MODIS recientes de este lote están cubiertas por nubes.")
        ultimo = validos[-1]
        return ResultadoPaso(
            resumen=resumenes.resumen_verdor(ultimo["ndvi"]),
            datos={
                "ndvi": ultimo["ndvi"],
                "evi": ultimo.get("evi"),
                "fecha_imagen": ultimo["date"],
                "cobertura": r.get("land_cover"),
                "fuente": "NASA MODIS MOD13Q1 (16 días, 250 m)",
            },
        )
