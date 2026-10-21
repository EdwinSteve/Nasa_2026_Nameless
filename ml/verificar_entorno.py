"""Revisa que la máquina de entrenamiento esté lista. Ejecutar desde ml/:

    python verificar_entorno.py

No modifica nada. Termina con código 1 si falta algo obligatorio.
"""
import importlib
import os
import platform
import sys
import time

from datos_tierra.__main__ import cargar_env

OBLIGATORIO, OPCIONAL = 'obligatorio', 'opcional'
resultados: list[tuple[str, bool, str, str]] = []


def revisar(nombre: str, nivel: str, prueba) -> None:
    try:
        detalle = prueba() or ''
        resultados.append((nombre, True, nivel, str(detalle)))
    except Exception as exc:  # cada revisión es independiente
        resultados.append((nombre, False, nivel, f'{type(exc).__name__}: {exc}'))


def python_version():
    if sys.version_info < (3, 11):
        raise RuntimeError(f'se necesita 3.11 o superior (recomendado 3.12); hay {platform.python_version()}')
    return platform.python_version()


def paquete(nombre):
    def prueba():
        modulo = importlib.import_module(nombre)
        return getattr(modulo, '__version__', 'ok')
    return prueba


def gpu_pytorch():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError(f'CUDA no disponible (torch {torch.__version__}, compilado para CUDA {torch.version.cuda})')
    nombre = torch.cuda.get_device_name(0)
    capacidad = torch.cuda.get_device_capability(0)
    memoria = torch.cuda.get_device_properties(0).total_memory / 1024**3
    x = torch.randn(4096, 4096, device='cuda', dtype=torch.bfloat16)
    x @ x  # calentamiento: la primera llamada inicializa cuBLAS y no debe entrar en la medición
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(20):
        x @ x
    torch.cuda.synchronize()
    tflops = 20 * 2 * 4096**3 / (time.perf_counter() - t0) / 1e12
    return f'{nombre}, sm_{capacidad[0]}{capacidad[1]}, {memoria:.1f} GB, CUDA {torch.version.cuda}, bf16 ≈ {tflops:.0f} TFLOPS'


def gpu_xgboost():
    import numpy as np
    import xgboost as xgb
    datos = xgb.DMatrix(np.random.rand(20000, 50), label=np.random.rand(20000))
    xgb.train({'device': 'cuda', 'tree_method': 'hist'}, datos, 10)
    return f'xgboost {xgb.__version__} entrenó en la GPU'


def earth_engine():
    import ee
    proyecto = os.environ.get('GEE_PROJECT')
    if not proyecto:
        raise RuntimeError('GEE_PROJECT vacío en .env')
    ee.Initialize(project=proyecto)
    assert ee.Number(1).add(1).getInfo() == 2
    return f'proyecto {proyecto}'


def api(url):
    def prueba():
        import httpx
        r = httpx.get(url, timeout=30)
        r.raise_for_status()
        return f'HTTP {r.status_code}'
    return prueba


def main() -> None:
    cargar_env()
    revisar('Python', OBLIGATORIO, python_version)
    for nombre in ('httpx', 'ee', 'numpy', 'polars', 'pyarrow', 'duckdb', 'numba', 'xgboost', 'lightgbm',
                   'sklearn', 'shap', 'optuna', 'mlflow', 'torch', 'onnxruntime'):
        revisar(f'paquete {nombre}', OBLIGATORIO, paquete(nombre))
    revisar('GPU con PyTorch', OBLIGATORIO, gpu_pytorch)
    revisar('GPU con XGBoost', OPCIONAL, gpu_xgboost)
    revisar('Earth Engine', OBLIGATORIO, earth_engine)
    revisar('API NASA POWER', OBLIGATORIO, api(
        'https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M&community=AG'
        '&latitude=3.22&longitude=-75.22&start=20240101&end=20240102&format=JSON'))
    revisar('API SoilGrids', OPCIONAL, api('https://rest.isric.org/soilgrids/v2.0/properties/layers'))
    revisar('API OpenTopoData (SRTM)', OBLIGATORIO, api('https://api.opentopodata.org/v1/srtm30m?locations=3.22,-75.22'))
    revisar('API NOAA ONI', OBLIGATORIO, api('https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt'))

    ancho = max(len(r[0]) for r in resultados)
    falla_obligatoria = False
    for nombre, ok, nivel, detalle in resultados:
        marca = '✅' if ok else ('❌' if nivel == OBLIGATORIO else '⚠️ ')
        falla_obligatoria |= not ok and nivel == OBLIGATORIO
        print(f'{marca} {nombre:<{ancho}}  {detalle}')
    print('\nListo para entrenar.' if not falla_obligatoria else '\nFalta algo obligatorio: revisa la guía ml/GUIA_MAQUINA_GPU.md.')
    sys.exit(1 if falla_obligatoria else 0)


if __name__ == '__main__':
    main()
