"""Modelo A: XGBoost en GPU sobre lote-fecha × cultivo (ml/README.md, sección 4).

    python -m surco_ml.modelos.gbdt                       # corte por tiempo: 1981-2014 / 2015-2018 / 2019-2024
    python -m surco_ml.modelos.gbdt --sin-huila           # corte por espacio: el Huila queda fuera del entrenamiento
    python -m surco_ml.modelos.gbdt --optuna 15           # busca hiperparámetros con 15 pruebas y luego entrena
    python -m surco_ml.modelos.gbdt --max-puntos 20       # prueba rápida con pocos puntos
    python -m surco_ml.modelos.gbdt --solo-registrar      # registra en MLflow una corrida ya guardada

Un modelo por etiqueta:
- puntaje y riego_mm: regresión por cuantiles (p10, p50, p90) en un solo árbol multi-salida.
- exito: clasificación binaria (P de completar el ciclo sin falla crítica).
- dias_estres: mediana (error absoluto).

Los datos se leen punto por punto con un DataIter y se cuantizan una sola vez (QuantileDMatrix):
las ~18 M de filas no tienen que caber en la RAM, y la misma matriz sirve para las 4 etiquetas
(las filas sin esa etiqueta van con peso 0).

Después de entrenar se calibra con el corte de VALIDACIÓN (calibracion.py): isotónica para
P(éxito) e intervalos conformales para puntaje y riego. La evaluación en el corte de prueba
compara contra dos líneas base: el oráculo con el clima medio y el promedio histórico del
puntaje en ese punto, fecha y cultivo (1981-2014), la más difícil de vencer.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import polars as pl
import xgboost as xgb

from ..evaluacion import metricas
from ..rutas import CORTES, DATASET, MODELOS, RAIZ, SEMILLA
from . import calibracion

CUANTILES = [0.1, 0.5, 0.9]
TAREAS = {
    'puntaje': {'objective': 'reg:quantileerror', 'quantile_alpha': CUANTILES},
    'exito': {'objective': 'binary:logistic', 'eval_metric': 'logloss'},
    'riego_mm': {'objective': 'reg:quantileerror', 'quantile_alpha': CUANTILES},
    'dias_estres': {'objective': 'reg:absoluteerror'},
}
# 0,05 con 3000 rondas se quedaba corto: el modelo de puntaje llegó al tope sin dejar de mejorar.
PARAMETROS = {
    'device': 'cuda', 'tree_method': 'hist', 'max_depth': 8, 'learning_rate': 0.1,
    'subsample': 0.8, 'colsample_bytree': 0.8, 'min_child_weight': 20, 'reg_lambda': 1.0,
    'max_bin': 256, 'seed': SEMILLA,
}
RONDAS, PARADA_TEMPRANA = 6000, 100
MUESTRA_SHAP = 20000
HIPERPARAMETROS = 'hiperparametros_modelo_a.json'   # dentro de --salida, junto a los modelos que los usan
PUNTOS_OPTUNA = 80


class Datos:
    """Índice del dataset: qué puntos hay, sus columnas y cómo armar la tabla de un punto."""

    def __init__(self, raiz: Path = DATASET, max_puntos: int | None = None):
        self.raiz = Path(raiz)
        self.cultivos = pl.read_parquet(self.raiz / 'cultivos.parquet')
        self.ids_cultivo = self.cultivos['cultivo_id'].to_list()
        self.puntos = sorted(p.stem for p in (self.raiz / 'etiquetas').glob('*.parquet'))[:max_puntos]
        if not self.puntos:
            raise SystemExit(f'No hay puntos en {self.raiz}: corre primero python -m surco_ml.dataset')
        muestra = pl.read_parquet(self.raiz / 'lote_fecha' / f'{self.puntos[0]}.parquet')
        self.cols_lote = [c for c in muestra.columns if c.startswith('f_')]
        self.cols_cultivo = [c for c in self.cultivos.columns if c.startswith('c_')]
        self.features = self.cols_lote + self.cols_cultivo + ['pc_taw_mm']
        self._c = self.cultivos.select(self.cols_cultivo).to_numpy().astype(np.float32)
        self._tipo = self.cultivos['c_tipo_ciclo'].to_numpy().astype(np.int8)

    def tabla(self, punto: str) -> tuple[np.ndarray, pl.DataFrame, str]:
        """(X, etiquetas, zona) de un punto: features del lote-fecha × ficha del cultivo."""
        lote = pl.read_parquet(self.raiz / 'lote_fecha' / f'{punto}.parquet')
        et = pl.read_parquet(self.raiz / 'etiquetas' / f'{punto}.parquet')
        fila = et['fila'].to_numpy()
        x = np.hstack([
            lote.select(self.cols_lote).to_numpy().astype(np.float32)[fila],
            self._c[et['cultivo'].to_numpy()],
            et['pc_taw_mm'].to_numpy().astype(np.float32)[:, None],
        ])
        return x, et, lote['zona'][0]

    def tipo_ciclo(self, et: pl.DataFrame) -> np.ndarray:
        return self._tipo[et['cultivo'].to_numpy()]


def _mascara(et: pl.DataFrame, zona: str, corte: str, sin_huila: bool) -> np.ndarray:
    a, b = CORTES[corte]
    anio = et['anio'].to_numpy()
    m = (anio >= a) & (anio <= b) & np.isfinite(et['puntaje'].to_numpy())
    if sin_huila and ((corte != 'test') == (zona == 'huila')):
        return np.zeros_like(m)
    return m


class Iterador(xgb.DataIter):
    """Entrega a XGBoost un punto a la vez y guarda sus etiquetas en el mismo orden de las filas."""

    def __init__(self, datos: Datos, puntos: list[str], corte: str, sin_huila: bool):
        self.datos, self.puntos, self.corte, self.sin_huila = datos, puntos, corte, sin_huila
        self.i = 0
        self._etiquetas: dict[int, dict[str, np.ndarray]] = {}
        super().__init__(cache_prefix=None)

    def next(self, entrada) -> bool:
        while self.i < len(self.puntos):
            i = self.i
            x, et, zona = self.datos.tabla(self.puntos[i])
            self.i += 1
            m = _mascara(et, zona, self.corte, self.sin_huila)
            if not m.any():
                continue
            if i not in self._etiquetas:  # XGBoost recorre los datos más de una vez
                self._etiquetas[i] = {k: et[k].to_numpy()[m] for k in TAREAS} | {'tipo_ciclo': self.datos.tipo_ciclo(et)[m]}
            entrada(data=x[m])
            return True
        return False

    def reset(self) -> None:
        self.i = 0

    def etiquetas(self) -> dict[str, np.ndarray]:
        orden = sorted(self._etiquetas)
        return {k: np.concatenate([self._etiquetas[i][k] for i in orden]) for k in self._etiquetas[orden[0]]}


def matrices(datos: Datos, puntos: list[str], sin_huila: bool):
    """(dtrain, etiquetas de train), (dvalid, etiquetas de validación): se construyen una sola vez."""
    t0 = time.monotonic()
    it_t = Iterador(datos, puntos, 'train', sin_huila)
    dtrain = xgb.QuantileDMatrix(it_t, max_bin=PARAMETROS['max_bin'])
    it_v = Iterador(datos, puntos, 'valid', sin_huila)
    dvalid = xgb.QuantileDMatrix(it_v, ref=dtrain)
    print(f'  matrices: {dtrain.num_row():,} filas de entrenamiento y {dvalid.num_row():,} de validación '
          f'({time.monotonic() - t0:.0f} s)', flush=True)
    return (dtrain, it_t.etiquetas()), (dvalid, it_v.etiquetas())


def usar_etiqueta(d: xgb.DMatrix, et: dict[str, np.ndarray], tarea: str) -> int:
    """Pone la etiqueta de la tarea; las filas sin dato (p. ej. riego sin Kc) van con peso 0."""
    y = et[tarea]
    ok = np.isfinite(y)
    d.set_info(label=np.where(ok, y, 0.0).astype(np.float32), weight=ok.astype(np.float32))
    return int(ok.sum())


def entrenar(train, valid, tarea: str, parametros: dict, rondas: int = RONDAS, verbose: int | bool = 250) -> xgb.Booster:
    (dtrain, et_t), (dvalid, et_v) = train, valid
    n_t, n_v = usar_etiqueta(dtrain, et_t, tarea), usar_etiqueta(dvalid, et_v, tarea)
    t0 = time.monotonic()
    modelo = xgb.train({**parametros, **TAREAS[tarea]}, dtrain, rondas, evals=[(dvalid, 'valid')],
                       early_stopping_rounds=PARADA_TEMPRANA, verbose_eval=verbose)
    if verbose:
        print(f'  {tarea}: {n_t:,} filas, {modelo.best_iteration + 1} árboles en {time.monotonic() - t0:.0f} s', flush=True)
    return modelo


def firma(datos: Datos, parametros: dict, sin_huila: bool, tarea: str) -> str:
    """Identifica lo que produjo un modelo: si cambia algo, el modelo guardado no sirve y se reentrena."""
    import hashlib
    manifiesto = (datos.raiz / 'manifiesto.json').read_text(encoding='utf-8')
    base = json.dumps({'parametros': parametros, 'tarea': TAREAS[tarea], 'rondas': RONDAS, 'parada': PARADA_TEMPRANA,
                       'puntos': datos.puntos, 'features': datos.features, 'sin_huila': sin_huila,
                       'manifiesto': manifiesto, 'cortes': CORTES}, sort_keys=True)
    return hashlib.sha256(base.encode()).hexdigest()[:16]


def entrenar_o_cargar(datos: Datos, train, valid, tarea: str, parametros: dict, sin_huila: bool, destino: Path) -> xgb.Booster:
    """Guarda cada modelo apenas termina. Si se corta la corrida, el mismo comando carga los que ya están."""
    ruta, registro = destino / f'modelo_a_{tarea}.ubj', destino / 'avance.json'
    avance = json.loads(registro.read_text(encoding='utf-8')) if registro.exists() else {}
    huella = firma(datos, parametros, sin_huila, tarea)
    if ruta.exists() and avance.get(tarea) == huella:
        modelo = xgb.Booster()
        modelo.load_model(ruta)
        modelo.set_param({'device': PARAMETROS['device']})
        # El guardado final lleva los nombres de las features; las matrices de entrenamiento no
        modelo.feature_names, modelo.feature_types = None, None
        print(f'  {tarea}: ya estaba entrenado ({modelo.best_iteration + 1} árboles), se carga de {ruta.name}', flush=True)
        return modelo
    modelo = entrenar(train, valid, tarea, parametros)
    destino.mkdir(parents=True, exist_ok=True)
    modelo.save_model(ruta)
    avance[tarea] = huella
    registro.write_text(json.dumps(avance, indent=2), encoding='utf-8')
    return modelo


def _predecir(modelo: xgb.Booster, d: xgb.DMatrix) -> np.ndarray:
    return modelo.predict(d, iteration_range=(0, modelo.best_iteration + 1))


def calibrar(modelos: dict[str, xgb.Booster], valid) -> dict:
    """Ajusta la calibración con las predicciones del corte de validación."""
    dvalid, et = valid
    p = _predecir(modelos['puntaje'], dvalid)
    r = _predecir(modelos['riego_mm'], dvalid)
    return {
        'exito_isotonica': calibracion.ajustar_isotonica(_predecir(modelos['exito'], dvalid), et['exito']),
        'puntaje_conformal': calibracion.ajustar_conformal(et['puntaje'], p[:, 0], p[:, 2], et['tipo_ciclo']),
        'riego_conformal': calibracion.ajustar_conformal(et['riego_mm'], r[:, 0], r[:, 2], et['tipo_ciclo']),
    }


def optimizar(datos: Datos, sin_huila: bool, pruebas: int, ruta: Path) -> dict:
    """Optuna sobre el modelo de puntaje con una submuestra fija de puntos; guarda los mejores parámetros.

    Profundidad 5-8 y tasa 0,05-0,25: con profundidad 8 y tasa 0,05 el modelo de puntaje pesaba 150 MB.
    """
    import optuna
    paso = max(1, len(datos.puntos) // PUNTOS_OPTUNA)
    puntos = datos.puntos[::paso]
    print(f'Optuna: {pruebas} pruebas con {len(puntos)} puntos', flush=True)
    train, valid = matrices(datos, puntos, sin_huila)

    def objetivo(trial):
        parametros = {**PARAMETROS,
                      'max_depth': trial.suggest_int('max_depth', 5, 8),
                      'learning_rate': trial.suggest_float('learning_rate', 0.05, 0.25, log=True),
                      'min_child_weight': trial.suggest_float('min_child_weight', 5, 300, log=True),
                      'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                      'colsample_bytree': trial.suggest_float('colsample_bytree', 0.4, 1.0),
                      'reg_lambda': trial.suggest_float('reg_lambda', 0.1, 30, log=True)}
        t0 = time.monotonic()
        modelo = entrenar(train, valid, 'puntaje', parametros, rondas=4000, verbose=False)
        trial.set_user_attr('arboles', modelo.best_iteration + 1)
        print(f'  prueba {trial.number}: pinball {modelo.best_score:.5f}, {modelo.best_iteration + 1} árboles, '
              f'{time.monotonic() - t0:.0f} s, {trial.params}', flush=True)
        return modelo.best_score

    # Cada prueba queda en SQLite: si se corta (p. ej. se va la luz), el mismo comando continúa donde iba
    ruta.parent.mkdir(parents=True, exist_ok=True)
    almacen = f"sqlite:///{(ruta.parent / 'optuna.db').as_posix()}"
    nombre = f"modelo_a_{'espacio' if sin_huila else 'tiempo'}_{len(puntos)}p"
    estudio = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=SEMILLA),
                                  storage=almacen, study_name=nombre, load_if_exists=True)
    hechas = len([t for t in estudio.trials if t.state == optuna.trial.TrialState.COMPLETE])
    if not estudio.trials:
        estudio.enqueue_trial({k: PARAMETROS[k] for k in ('max_depth', 'learning_rate', 'min_child_weight',
                                                          'subsample', 'colsample_bytree', 'reg_lambda')})
    if hechas:
        print(f'  Optuna retoma el estudio {nombre}: {hechas} pruebas ya hechas', flush=True)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    estudio.optimize(objetivo, n_trials=max(0, pruebas - hechas))
    mejor = {**estudio.best_params, 'pinball_validacion': estudio.best_value,
             'arboles_en_submuestra': estudio.best_trial.user_attrs['arboles'], 'puntos': len(puntos), 'pruebas': pruebas}
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(mejor, indent=2), encoding='utf-8')
    print(f'Mejores parámetros (guardados en {ruta}): {mejor}', flush=True)
    del train, valid
    return mejor


def parametros_finales(ruta: Path) -> dict:
    """Los de la última búsqueda de Optuna en esta carpeta de salida; si no hay, los de PARAMETROS."""
    if ruta.exists():
        guardados = json.loads(ruta.read_text(encoding='utf-8'))
        return {**PARAMETROS, **{k: v for k, v in guardados.items() if k in PARAMETROS}}
    return dict(PARAMETROS)


def _historico(et: pl.DataFrame) -> pl.DataFrame:
    """Línea base fuerte: media del puntaje, del éxito y del riego en 1981-2014 por fecha del año y cultivo."""
    a, b = CORTES['train']
    return (et.filter((pl.col('anio') >= a) & (pl.col('anio') <= b)).with_columns(ranura=pl.col('fila') % 24)
            .group_by('ranura', 'cultivo').agg(pl.col('puntaje').mean().alias('puntaje_hist'),
                                                pl.col('exito').mean().alias('exito_hist'),
                                                pl.col('riego_mm').mean().alias('riego_hist'),
                                                pl.col('dias_estres').mean().alias('estres_hist')))


def evaluar(datos: Datos, modelos: dict[str, xgb.Booster], cal: dict, sin_huila: bool) -> tuple[dict, np.ndarray]:
    """Métricas en el corte de prueba: modelo crudo y calibrado contra las dos líneas base."""
    columnas = ('y', 'p10', 'p50', 'p90', 'c10', 'c90', 'clim', 'hist', 'grupo', 'ye', 'prob', 'prob_cal',
                'e_clim', 'e_hist', 'yr', 'r10', 'r50', 'r90', 'rc10', 'rc90', 'r_clim', 'r_hist',
                'ys', 's50', 's_clim', 's_hist')
    acum = {k: [] for k in columnas}
    muestra_shap = []
    rng = np.random.default_rng(SEMILLA)
    for n, punto in enumerate(datos.puntos):
        x, et, zona = datos.tabla(punto)
        m = _mascara(et, zona, 'test', sin_huila)
        if not m.any():
            continue
        hist = _historico(et)
        x, et = x[m], et.filter(pl.Series(m)).with_columns(ranura=pl.col('fila') % 24)
        et = et.join(hist, on=['ranura', 'cultivo'], how='left', maintain_order='left')
        d = xgb.DMatrix(x)
        tipo = datos.tipo_ciclo(et)
        p, r = _predecir(modelos['puntaje'], d), _predecir(modelos['riego_mm'], d)
        prob = _predecir(modelos['exito'], d)
        c10, c90 = calibracion.aplicar_conformal(p[:, 0], p[:, 1], p[:, 2], tipo, cal['puntaje_conformal'], 0.0, 1.0)
        rc10, rc90 = calibracion.aplicar_conformal(r[:, 0], r[:, 1], r[:, 2], tipo, cal['riego_conformal'], 0.0)
        valores = {
            'y': et['puntaje'], 'p10': p[:, 0], 'p50': p[:, 1], 'p90': p[:, 2], 'c10': c10, 'c90': c90,
            'clim': et['puntaje_clim'], 'hist': et['puntaje_hist'], 'grupo': n * 100000 + et['fila'].to_numpy(),
            'ye': et['exito'], 'prob': prob, 'prob_cal': calibracion.aplicar_isotonica(prob, cal['exito_isotonica']),
            'e_clim': et['exito_frec_clim'], 'e_hist': et['exito_hist'],
            'yr': et['riego_mm'], 'r10': r[:, 0], 'r50': r[:, 1], 'r90': r[:, 2], 'rc10': rc10, 'rc90': rc90,
            'r_clim': et['riego_mm_clim'], 'r_hist': et['riego_hist'],
            'ys': et['dias_estres'], 's50': _predecir(modelos['dias_estres'], d),
            's_clim': et['dias_estres_clim'], 's_hist': et['estres_hist'],
        }
        for k, v in valores.items():
            acum[k].append(np.asarray(v.to_numpy() if isinstance(v, pl.Series) else v, dtype=np.float64))
        muestra_shap.append(x[rng.random(len(x)) < 0.02])
    a = {k: np.concatenate(v) for k, v in acum.items()}
    ok = np.isfinite(a['y']) & np.isfinite(a['hist'])
    r = {
        'test_filas': int(len(a['y'])),
        'puntaje_mae_modelo': metricas.mae(a['y'], a['p50']),
        'puntaje_mae_climatologia': metricas.mae(a['y'], a['clim']),
        'puntaje_mae_historico': metricas.mae(a['y'], a['hist']),
        'puntaje_correlacion_anomalias': float(np.corrcoef(a['y'][ok] - a['hist'][ok], a['p50'][ok] - a['hist'][ok])[0, 1]),
        'puntaje_pinball_p10': metricas.pinball(a['y'], a['p10'], 0.1),
        'puntaje_pinball_p50': metricas.pinball(a['y'], a['p50'], 0.5),
        'puntaje_pinball_p90': metricas.pinball(a['y'], a['p90'], 0.9),
        'puntaje_cobertura_cruda': metricas.cobertura(a['y'], a['p10'], a['p90']),
        'puntaje_cobertura_calibrada': metricas.cobertura(a['y'], a['c10'], a['c90']),
        'puntaje_bajo_p10_calibrado': float(np.mean(a['y'] < a['c10'])),
        'puntaje_sobre_p90_calibrado': float(np.mean(a['y'] > a['c90'])),
        'puntaje_ancho_intervalo_calibrado': float(np.mean(a['c90'] - a['c10'])),
        'ndcg3_modelo': metricas.ndcg_at_k(a['y'], a['p50'], a['grupo']),
        'ndcg3_climatologia': metricas.ndcg_at_k(a['y'], a['clim'], a['grupo']),
        'ndcg3_historico': metricas.ndcg_at_k(a['y'], np.nan_to_num(a['hist']), a['grupo']),
        'exito_tasa_real': float(np.nanmean(a['ye'])),
        'exito_brier_modelo': metricas.brier(a['ye'], a['prob']),
        'exito_brier_calibrado': metricas.brier(a['ye'], a['prob_cal']),
        'exito_brier_climatologia': metricas.brier(a['ye'], a['e_clim']),
        'exito_brier_historico': metricas.brier(a['ye'], a['e_hist']),
        'exito_ece_modelo': metricas.ece(a['ye'], a['prob']),
        'exito_ece_calibrado': metricas.ece(a['ye'], a['prob_cal']),
        'exito_ece_climatologia': metricas.ece(a['ye'], a['e_clim']),
        'riego_mae_modelo': metricas.mae(a['yr'], a['r50']),
        'riego_mae_climatologia': metricas.mae(a['yr'], a['r_clim']),
        'riego_mae_historico': metricas.mae(a['yr'], a['r_hist']),
        'riego_cobertura_cruda': metricas.cobertura(a['yr'], a['r10'], a['r90']),
        'riego_cobertura_calibrada': metricas.cobertura(a['yr'], a['rc10'], a['rc90']),
        'estres_mae_modelo': metricas.mae(a['ys'], a['s50']),
        'estres_mae_climatologia': metricas.mae(a['ys'], a['s_clim']),
        'estres_mae_historico': metricas.mae(a['ys'], a['s_hist']),
    }
    r['le_gana_a_la_climatologia'] = bool(
        r['puntaje_mae_modelo'] < r['puntaje_mae_climatologia'] and r['ndcg3_modelo'] > r['ndcg3_climatologia']
        and r['exito_brier_calibrado'] < r['exito_brier_climatologia'])
    r['le_gana_al_historico'] = bool(
        r['puntaje_mae_modelo'] < r['puntaje_mae_historico'] and r['ndcg3_modelo'] > r['ndcg3_historico']
        and r['exito_brier_calibrado'] < r['exito_brier_historico'])
    return r, np.concatenate(muestra_shap)[:MUESTRA_SHAP]


def shap_global(modelo: xgb.Booster, x: np.ndarray, nombres: list[str], salida: int | None = None) -> list[tuple[str, float]]:
    """Media de |SHAP| por feature (TreeSHAP en la GPU de XGBoost)."""
    contrib = modelo.predict(xgb.DMatrix(x, feature_names=nombres), pred_contribs=True,
                             iteration_range=(0, modelo.best_iteration + 1))
    if contrib.ndim == 3:  # multi-salida: (filas, salidas, features+1)
        contrib = contrib[:, 1 if salida is None else salida, :]
    importancia = np.abs(contrib[:, :-1]).mean(0)
    orden = np.argsort(-importancia)
    return [(nombres[i], float(importancia[i])) for i in orden[:25]]


def registrar(destino: Path) -> None:
    """Registra en MLflow una corrida ya entrenada a partir de su informe.json.

    Usa SQLite (ml/mlflow.db): desde MLflow 3 el almacén en carpetas (./mlruns) está congelado.
    Los .ubj no se copian a MLflow (pesan cientos de MB): se registra dónde quedaron.
    Si MLflow falla, solo avisa: los modelos y el informe ya están guardados.
    """
    informe = json.loads((destino / 'informe.json').read_text(encoding='utf-8'))
    try:
        import mlflow
        mlflow.set_tracking_uri(f"sqlite:///{(RAIZ / 'ml/mlflow.db').as_posix()}")
        if mlflow.get_experiment_by_name('surco_modelo_a') is None:
            mlflow.create_experiment('surco_modelo_a', artifact_location=(RAIZ / 'ml/mlruns').as_uri())
        mlflow.set_experiment('surco_modelo_a')
        with mlflow.start_run(run_name=informe['corrida']):
            mlflow.log_params({**informe['parametros'], 'puntos': informe['puntos'], 'features': len(informe['features']),
                               'corrida': informe['corrida'], 'modelos': str(destino)})
            mlflow.log_params({f'arboles_{k}': v for k, v in informe['arboles'].items()})
            mlflow.log_params({f'catalogo_{k}': v for k, v in informe['catalogo_version'].items()})
            mlflow.log_metrics({k: float(v) for k, v in informe['resultados'].items()})
            for archivo in ('informe.json', 'calibracion.json'):
                if (destino / archivo).exists():
                    mlflow.log_artifact(str(destino / archivo))
        print(f"Registrado en MLflow: {informe['corrida']}")
    except Exception as exc:
        print(f'Aviso: no se pudo registrar en MLflow ({type(exc).__name__}: {exc}). Los modelos están en {destino}')


def main() -> None:
    ap = argparse.ArgumentParser(prog='surco_ml.modelos.gbdt', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', default=str(DATASET))
    ap.add_argument('--sin-huila', action='store_true', help='Corte por espacio: entrenar sin el Huila y probar en el Huila')
    ap.add_argument('--max-puntos', type=int, default=None)
    ap.add_argument('--salida', default=str(MODELOS), help='Carpeta de los modelos exportados')
    ap.add_argument('--optuna', type=int, default=0, metavar='N', help='Buscar hiperparámetros con N pruebas antes de entrenar')
    ap.add_argument('--sin-mlflow', action='store_true')
    ap.add_argument('--solo-registrar', action='store_true', help='No entrena: registra en MLflow la corrida ya guardada')
    a = ap.parse_args()

    corrida = 'espacio_sin_huila' if a.sin_huila else 'tiempo'
    if a.solo_registrar:
        registrar(Path(a.salida) / corrida)
        return

    datos = Datos(Path(a.dataset), a.max_puntos)
    ruta_hiper = Path(a.salida) / HIPERPARAMETROS
    if a.optuna:
        optimizar(datos, a.sin_huila, a.optuna, ruta_hiper)
    parametros = parametros_finales(ruta_hiper)
    print(f'Modelo A ({corrida}): {len(datos.puntos)} puntos, {len(datos.features)} features, parámetros {parametros}', flush=True)

    destino = Path(a.salida) / corrida
    train, valid = matrices(datos, datos.puntos, a.sin_huila)
    modelos = {tarea: entrenar_o_cargar(datos, train, valid, tarea, parametros, a.sin_huila, destino) for tarea in TAREAS}
    cal = calibrar(modelos, valid)
    del train, valid
    resultados, x_shap = evaluar(datos, modelos, cal, a.sin_huila)
    for modelo in modelos.values():
        modelo.feature_names = datos.features
    importancia = {k: shap_global(modelos[k], x_shap, datos.features) for k in ('puntaje', 'exito')}

    tamanos = {}
    for etiqueta, modelo in modelos.items():
        modelo.set_param({'device': 'cpu'})   # el backend predice en CPU
        ruta = destino / f'modelo_a_{etiqueta}.ubj'
        modelo.save_model(ruta)
        tamanos[etiqueta] = round(ruta.stat().st_size / 1e6, 1)
    (destino / 'calibracion.json').write_text(json.dumps(cal, indent=2), encoding='utf-8')
    manifiesto = json.loads((datos.raiz / 'manifiesto.json').read_text(encoding='utf-8'))
    informe = {'corrida': corrida, 'puntos': len(datos.puntos), 'features': datos.features,
               'cultivos': datos.ids_cultivo, 'resultados': resultados, 'shap_top': importancia,
               'parametros': parametros, 'arboles': {k: m.best_iteration + 1 for k, m in modelos.items()},
               'tamano_mb': tamanos, 'catalogo_version': manifiesto['cultivos']}
    (destino / 'informe.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')

    if not a.sin_mlflow:
        registrar(destino)

    print(json.dumps(resultados, indent=2))
    print('\nSHAP (puntaje):', ', '.join(f'{n} {v:.3f}' for n, v in importancia['puntaje'][:10]))
    print('Tamaño de los modelos (MB):', tamanos)
    print('Le gana a la climatología:', 'SÍ' if resultados['le_gana_a_la_climatologia'] else 'NO')
    print('Le gana al promedio histórico:', 'SÍ' if resultados['le_gana_al_historico'] else 'NO')
    print(f'Modelos en {destino}')


if __name__ == '__main__':
    main()
