"""Adaptador del puerto ModeloPredictivo sobre surco_ml (ml/surco_ml), el modelo A entrenado en GPU.

Los modelos (.ubj) no se versionan: hay que copiarlos de la máquina de entrenamiento a
ml/modelos_exportados/<corrida>/. Sin ellos, disponible() devuelve el motivo y la API responde 503.
"""
import asyncio
import os
from datetime import date


class ModeloSurco:
    def __init__(self, corrida: str = "tiempo", gee_project: str | None = None) -> None:
        self.corrida = corrida
        if gee_project:
            os.environ.setdefault("GEE_PROJECT", gee_project)

    def disponible(self) -> str | None:
        try:
            from surco_ml import predecir
        except ImportError:
            return "El modelo predictivo no está instalado en el servidor (pip install -e '../ml[gee,modelo]')."
        try:
            predecir.verificar_modelo(self.corrida)
        except predecir.ModeloNoDisponible as exc:
            return str(exc)
        return None

    def ultima_fecha(self) -> date:
        from surco_ml import predecir

        return predecir.ultima_fecha_de_siembra()

    async def recomendar(self, lat: float, lon: float, fecha: date) -> dict:
        from surco_ml import predecir

        # Solo hasta el día de la siembra: el modelo no usa nada posterior (sin fuga de información)
        try:
            datos = await predecir.bajar_datos(lat, lon, fecha, suelo_via="gee")
        except Exception:  # sin Earth Engine el suelo sale de la API de ISRIC
            datos = await predecir.bajar_datos(lat, lon, fecha, suelo_via="rest")
        return await asyncio.to_thread(predecir.recomendar, datos, fecha, self.corrida, False)
