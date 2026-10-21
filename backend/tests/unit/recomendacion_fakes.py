"""Dobles en memoria para el módulo recomendacion."""
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import date

from app.modules.recomendacion.domain.entity import LoteRecomendacion
from tests.unit.diagnostico_fakes import AHORA, DUENO, LOTE

LOTE_R = LoteRecomendacion(lote_id=LOTE.lote_id, nombre=LOTE.nombre, lat=LOTE.lat, lon=LOTE.lon)
ULTIMA = date(2026, 10, 1)


def resultado(*cultivos) -> dict:
    """Misma forma que surco_ml.predecir.recomendar."""
    return {
        "fecha": "2026-10-01", "corrida": "tiempo", "arboles": {}, "n_features": 131, "elevacion_m": 464.2,
        "ph_0_30": 5.84, "eficiencia_riego": 0.9,
        "features_resumen": {"f_lluvia_90": 180.5, "f_t_media_90": 27.1, "f_oni": 1.8},
        "resultados": list(cultivos),
    }


def cultivo(id_, nombre, p50, prob=0.8, riego=300.0, pasa=True, motivo=None):
    return {
        "cultivo": nombre, "id": id_, "pasa_filtros": pasa, "motivo": motivo,
        "puntaje_p50": p50, "puntaje_p10": p50 - 0.1, "puntaje_p90": min(p50 + 0.1, 1.0), "prob_exito": prob,
        "riego_neto_mm": riego, "riego_p10_mm": riego, "riego_p90_mm": riego,
        "dias_estres": None if riego is None else 3.0, "dias_ciclo": 120,
    }


RESULTADO = resultado(
    cultivo("frijol", "Fríjol", 0.62),
    cultivo("maiz", "Maíz", 0.81, prob=0.77, riego=306.0),
    cultivo("mango", "Mango", 0.70, riego=None),
    cultivo("papa", "Papa", 0.95, pasa=False, motivo="altitud 464 m fuera de 2000-3500 m"),
)


class LotesFalsos:
    async def para_recomendacion(self, propietario_id, lote_id):
        return LOTE_R if (propietario_id, lote_id) == (DUENO, LOTE_R.lote_id) else None


class RecomendacionesFalsas:
    def __init__(self) -> None:
        self.por_id: dict = {}

    async def crear(self, recomendacion):
        recomendacion = replace(recomendacion, created_at=AHORA)
        self.por_id[recomendacion.id] = recomendacion
        return recomendacion

    async def obtener(self, recomendacion_id):
        return self.por_id.get(recomendacion_id)

    async def terminar(self, recomendacion_id, estado, ahora, resultado=None, error=None):
        self.por_id[recomendacion_id] = replace(
            self.por_id[recomendacion_id], estado=estado, terminado_en=ahora, resultado=resultado, error=error
        )


class UnitOfWorkFalso:
    async def confirmar(self) -> None:
        pass


def fabrica(recomendaciones: RecomendacionesFalsas):
    @asynccontextmanager
    async def abrir():
        yield recomendaciones, UnitOfWorkFalso()

    return abrir


class ModeloFalso:
    corrida = "tiempo"

    def __init__(self, motivo: str | None = None, falla: bool = False, resultado_: dict = RESULTADO) -> None:
        self.motivo, self.falla, self.resultado = motivo, falla, resultado_
        self.pedidos: list[tuple] = []

    def disponible(self):
        return self.motivo

    def ultima_fecha(self):
        return ULTIMA

    async def recomendar(self, lat, lon, fecha):
        self.pedidos.append((lat, lon, fecha))
        if self.falla:
            raise RuntimeError("Earth Engine no respondió")
        return self.resultado


