"""Predicción del modelo A para un lote y una fecha de siembra: lo mismo que hará el backend.

    python -m surco_ml.predecir --lat 1.82 --lon -76.02 --fecha 2023-03-01
    python -m surco_ml.predecir --finca pitalito-cafe --fecha 2023-03-01 --top 8
    python -m surco_ml.predecir --finca campoalegre-arroz --fecha 2022-09-16 --sin-real

Pasos:
1. Baja los datos del punto con datos_tierra (POWER, DEM, ENSO, SMAP, IMERG; suelo por Earth Engine).
2. Calcula las 131 features del día de la siembra con el MISMO código del entrenamiento.
3. Predice con los modelos de ml/modelos_exportados/<corrida>/ y aplica su calibracion.json.
4. Aplica los filtros duros del catálogo: altitud de la zona de producción y pH absoluto del suelo.
5. Ordena los cultivos por puntaje y muestra el riego que necesita cada uno.
6. Si el ciclo ya ocurrió, corre el oráculo con el clima REAL y compara (lo que de verdad pasó).

La fecha debe ser un 1 o un 16 (las fechas de siembra del modelo) y no posterior a los datos de POWER.
"""
import argparse
import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx
import numpy as np
import xgboost as xgb

from datos_tierra import suelo as suelo_dt
from datos_tierra import unificar
from datos_tierra.__main__ import cargar_env
from datos_tierra.fuentes import soilgrids, soilgrids_gee

from . import catalogo
from .features import construir
from .modelos import calibracion
from .oraculo import etiquetas, simulador
from .rutas import DIAS_SIEMBRA, MODELOS, RAIZ
from .series import desde_json

FINCAS = RAIZ / 'data/fincas_demo.json'
FUENTES = ('power', 'dem', 'enso', 'smap', 'imerg')
EFICIENCIA_RIEGO = 0.90   # la misma del ejemplo del motor agronómico (goteo/aspersión bien manejados)
DIAS_MAX_CICLO = 600      # la piña dura ~525 días


async def bajar_datos(lat: float, lon: float, fin: date, suelo_via: str) -> dict:
    cargar_env()
    async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=30)) as cliente:
        datos = await unificar.ejecutar(cliente, lat, lon, '1981-01-01', fin, fuentes=FUENTES)
        crudo = (await asyncio.to_thread(soilgrids_gee.descargar, lat, lon) if suelo_via == 'gee'
                 else await soilgrids.descargar(cliente, lat, lon))
    datos['soil'] = suelo_dt.procesar(crudo)
    return datos


def siembras_de_la_serie(serie, ultima: date) -> dict[str, np.ndarray]:
    """Todas las fechas 1 y 16 de la serie hasta `ultima`: la climatología de las features las necesita."""
    filas = []
    for anio in range(1981, ultima.year + 1):
        for mes in range(1, 13):
            for dia in DIAS_SIEMBRA:
                d = date(anio, mes, dia)
                i = serie.indice(d)
                if d <= ultima and 0 <= i < len(serie.fechas):
                    filas.append((i, anio, mes, dia, (mes - 1) * len(DIAS_SIEMBRA) + DIAS_SIEMBRA.index(dia)))
    idx, anio, mes, dia, ranura = (np.array(c) for c in zip(*filas))
    return {'idx': idx, 'anio': anio, 'mes': mes, 'dia': dia, 'ranura': ranura}


def filtros_duros(lista: list[dict], elevacion: float, ph: float | None) -> list[str | None]:
    """Motivo por el que el catálogo descarta cada cultivo (None = pasa). El modelo nunca salta estas reglas."""
    motivos = []
    for c in lista:
        alt = c['zona_produccion']['altitud_msnm']
        r_ph = c['requerimientos_cultivo']['suelo']['ph']
        if not alt['min'] <= elevacion <= alt['max']:
            motivos.append(f"altitud {elevacion:.0f} m fuera de {alt['min']}-{alt['max']} m")
        elif ph is not None and not r_ph['min_absoluto'] <= ph <= r_ph['max_absoluto']:
            motivos.append(f"pH {ph:.1f} fuera de {r_ph['min_absoluto']}-{r_ph['max_absoluto']}")
        else:
            motivos.append(None)
    return motivos


def main() -> None:
    # La consola de Windows usa cp1252 y no imprime todos los caracteres (tildes en tablas, flechas)
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, 'reconfigure'):
            flujo.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(prog='surco_ml.predecir', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lat', type=float)
    ap.add_argument('--lon', type=float)
    ap.add_argument('--finca', help='id de data/fincas_demo.json, en lugar de --lat/--lon')
    ap.add_argument('--fecha', required=True, help='Fecha de siembra AAAA-MM-DD (día 1 o 16)')
    ap.add_argument('--top', type=int, default=10)
    ap.add_argument('--corrida', default='tiempo', help='Carpeta de ml/modelos_exportados con los modelos')
    ap.add_argument('--suelo', choices=('gee', 'rest'), default='gee')
    ap.add_argument('--sin-real', action='store_true', help='No comparar con lo que pasó en el ciclo')
    ap.add_argument('--json', help='Guardar el resultado completo en este archivo')
    a = ap.parse_args()

    nombre = 'punto'
    if a.finca:
        finca = next(f for f in json.loads(FINCAS.read_text(encoding='utf-8'))['fincas'] if f['id'] == a.finca)
        a.lat, a.lon, nombre = finca['lat'], finca['lon'], finca['nombre']
    fecha = date.fromisoformat(a.fecha)
    if fecha.day not in DIAS_SIEMBRA:
        raise SystemExit(f'La fecha debe ser un día {DIAS_SIEMBRA}: el modelo se entrenó con siembras del 1 y el 16.')

    # --- 1. Datos del punto: hasta el fin del ciclo más largo, si ya ocurrió (para comparar con lo real)
    fin = min(fecha + timedelta(days=DIAS_MAX_CICLO), date.today() - timedelta(days=10))
    if fin < fecha:
        raise SystemExit('La fecha es posterior a los datos disponibles de POWER.')
    print(f'1. Bajando datos de {nombre} ({a.lat}, {a.lon}) de 1981 a {fin}...', flush=True)
    datos = asyncio.run(bajar_datos(a.lat, a.lon, fin, a.suelo))
    estados = {k: v['status'] for k, v in datos['sources'].items()}
    serie = desde_json(datos, 'prueba')
    print(f'   fuentes {estados} | elevación {serie.elevacion_m:.0f} m | {len(serie.fechas)} días', flush=True)

    # --- 2. Features del día de la siembra (mismo código del entrenamiento)
    siembras = siembras_de_la_serie(serie, fecha)
    fila = int(np.where(siembras['idx'] == serie.indice(fecha))[0][0])
    feats = construir.construir(serie, siembras)
    lista = catalogo.cargar()
    arreglos = catalogo.a_arreglos(lista)
    taw = etiquetas.taw_por_cultivo(serie, arreglos)
    fichas = catalogo.features(lista)

    carpeta = MODELOS / a.corrida
    informe = json.loads((carpeta / 'informe.json').read_text(encoding='utf-8'))
    cal = json.loads((carpeta / 'calibracion.json').read_text(encoding='utf-8'))
    nombres = informe['features']
    n_c = len(lista)
    x = np.empty((n_c, len(nombres)), np.float32)
    for j, col in enumerate(nombres):
        if col.startswith('f_'):
            x[:, j] = feats[col][fila]
        elif col.startswith('c_'):
            x[:, j] = fichas[col]
        else:
            x[:, j] = taw
    resumen = {k: round(float(feats[k][fila]), 2) for k in ('f_t_media_90', 'f_lluvia_90', 'f_lluvia_365', 'f_oni',
                                                            'f_sm_raiz', 'f_clim_lluvia_210_media', 'f_clim_t_210_media')}
    print(f'2. Features del {fecha}: {len(nombres)} columnas | {resumen}', flush=True)

    # --- 3. Predicción + calibración
    d = xgb.DMatrix(x, feature_names=nombres)
    modelos = {}
    for t in ('puntaje', 'exito', 'riego_mm', 'dias_estres'):
        m = xgb.Booster()
        m.load_model(carpeta / f'modelo_a_{t}.ubj')
        m.set_param({'device': 'cpu'})
        modelos[t] = m
    p, r = modelos['puntaje'].predict(d), modelos['riego_mm'].predict(d)
    tipo = fichas['c_tipo_ciclo'].astype(int)
    p10, p90 = calibracion.aplicar_conformal(p[:, 0], p[:, 1], p[:, 2], tipo, cal['puntaje_conformal'], 0.0, 1.0)
    r10, r90 = calibracion.aplicar_conformal(r[:, 0], r[:, 1], r[:, 2], tipo, cal['riego_conformal'], 0.0)
    prob = calibracion.aplicar_isotonica(modelos['exito'].predict(d), cal['exito_isotonica'])
    estres = modelos['dias_estres'].predict(d)
    sin_agua = ~arreglos.tiene_agua | ~np.isfinite(taw)
    print(f"3. Predicción con los modelos '{a.corrida}' ({informe['arboles']} árboles), calibrada", flush=True)

    # --- 4. Filtros duros
    ph = (serie.suelo or {}).get('summary', {}).get('0-30cm', {}).get('phh2o', {}).get('Q0.5')
    motivos = filtros_duros(lista, serie.elevacion_m, ph)
    print(f"4. Filtros duros: {sum(m is None for m in motivos)} de {n_c} cultivos pasan "
          f"(altitud {serie.elevacion_m:.0f} m, pH 0-30 cm {ph if ph is None else round(ph, 1)})", flush=True)

    # --- 6. Lo que de verdad pasó (oráculo con el clima real)
    real = None
    if not a.sin_real:
        r_real = simulador.simular(serie.v, np.array([serie.indice(fecha)]), arreglos, taw)
        if np.isfinite(r_real['puntaje'][0]).any():
            real = {k: v[0] for k, v in r_real.items()}

    # --- 5. Ranking
    resultados = []
    for i, c in enumerate(lista):
        fila_r = {
            'cultivo': c['nombre'], 'id': c['_id'], 'pasa_filtros': motivos[i] is None, 'motivo': motivos[i],
            'puntaje_p50': float(p[i, 1]), 'puntaje_p10': float(p10[i]), 'puntaje_p90': float(p90[i]),
            'prob_exito': float(prob[i]),
            'riego_neto_mm': None if sin_agua[i] else float(max(r[i, 1], 0)),
            'riego_p10_mm': None if sin_agua[i] else float(r10[i]), 'riego_p90_mm': None if sin_agua[i] else float(r90[i]),
            'dias_estres': None if sin_agua[i] else float(max(estres[i], 0)),
            'dias_ciclo': int(arreglos.dias_ciclo[i]),
        }
        if real is not None and np.isfinite(real['puntaje'][i]):
            fila_r.update(real_puntaje=float(real['puntaje'][i]), real_exito=float(real['exito'][i]),
                          real_riego_mm=None if np.isnan(real['riego_mm'][i]) else float(real['riego_mm'][i]))
        resultados.append(fila_r)
    ok = sorted([x for x in resultados if x['pasa_filtros']], key=lambda x: -x['puntaje_p50'])

    print(f'\n5. Recomendación para sembrar el {fecha} en {nombre}:\n')
    cab = f"{'#':>2}  {'Cultivo':<28} {'Puntaje (p10-p90)':<20} {'P(éxito)':>8}  {'Riego neto mm (p10-p90)':<24} {'m³/ha bruto':>11} {'Estrés':>7}"
    if real is not None:
        cab += f"   {'REAL: puntaje':>13} {'éxito':>5} {'riego':>6}"
    print(cab)
    print('-' * len(cab))
    for n, x in enumerate(ok[:a.top], 1):
        riego = '—' if x['riego_neto_mm'] is None else f"{x['riego_neto_mm']:.0f} ({x['riego_p10_mm']:.0f}-{x['riego_p90_mm']:.0f})"
        bruto = '—' if x['riego_neto_mm'] is None else f"{x['riego_neto_mm'] / EFICIENCIA_RIEGO * 10:,.0f}"
        est = '—' if x['dias_estres'] is None else f"{x['dias_estres']:.0f} d"
        linea = (f"{n:>2}  {x['cultivo'][:28]:<28} {x['puntaje_p50']:.2f} ({x['puntaje_p10']:.2f}-{x['puntaje_p90']:.2f})"
                 f"     {100 * x['prob_exito']:>6.0f} %  {riego:<24} {bruto:>11} {est:>7}")
        if 'real_puntaje' in x:
            rr = '—' if x['real_riego_mm'] is None else f"{x['real_riego_mm']:.0f}"
            linea += f"   {x['real_puntaje']:>13.2f} {'sí' if x['real_exito'] else 'no':>5} {rr:>6}"
        print(linea)
    descartados = [x for x in resultados if not x['pasa_filtros']]
    print(f"\nDescartados por el catálogo ({len(descartados)}): " + '; '.join(f"{x['cultivo']} ({x['motivo']})" for x in descartados[:8])
          + (' ...' if len(descartados) > 8 else ''))
    print(f'Riego bruto = neto / eficiencia {EFICIENCIA_RIEGO:.0%} x 10 (de mm a m3/ha). Es el total del ciclo, no por riego.')

    if real is not None:
        con_real = [x for x in ok if 'real_puntaje' in x]
        mejor_real = sorted(con_real, key=lambda x: -x['real_puntaje'])[:3]
        top_modelo = [x['id'] for x in ok[:3]]
        aciertos = sum(x['id'] in top_modelo for x in mejor_real)
        err = np.mean([abs(x['puntaje_p50'] - x['real_puntaje']) for x in con_real])
        dentro = np.mean([x['puntaje_p10'] <= x['real_puntaje'] <= x['puntaje_p90'] for x in con_real])
        print(f"\n6. Comparación con lo que pasó de verdad (oráculo con el clima real de ese ciclo):")
        print(f"   top 3 real: {', '.join(x['cultivo'] for x in mejor_real)} | coincide con el top 3 del modelo en {aciertos} de 3")
        print(f"   error medio del puntaje: {err:.3f} | puntaje real dentro del rango p10-p90 en el {100 * dentro:.0f} % de los cultivos")

    if a.json:
        Path(a.json).write_text(json.dumps({'lat': a.lat, 'lon': a.lon, 'fecha': a.fecha, 'resultados': resultados},
                                           ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\nResultado completo en {a.json}')


if __name__ == '__main__':
    main()
