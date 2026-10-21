"""Rutas del repo y parámetros fijos del dataset (sección 2 de ml/README.md)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CATALOGO = RAIZ / 'data/catalogo_cultivos_mongodb/datos/cultivos.json'
MOTOR_AGRONOMICO = RAIZ / 'scripts/data/agronomic_engine'
CRUDOS = RAIZ / 'data/raw/entrenamiento'
DATASET = RAIZ / 'data/processed/dataset'
MODELOS = RAIZ / 'ml/modelos_exportados'

SEMILLA = 7
ANIOS = (1981, 2024)
DIAS_SIEMBRA = (1, 16)                         # 24 fechas por año: el 1 y el 16 de cada mes
CORTES = {'train': (1981, 2014), 'valid': (2015, 2018), 'test': (2019, 2024)}
