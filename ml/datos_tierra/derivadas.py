"""Variables físicas derivadas de los datos crudos. Son las mismas en entrenamiento e inferencia.

- Temperatura corregida por elevación (ADR 0002).
- ET0 FAO-56 Penman-Monteith (informe 08, sección 4.2) y Hargreaves como respaldo (4.3).
- Lluvia fusionada: IMERG cuando existe, si no POWER.
- Climatología por día del año: lo que el modelo sabe del futuro el día de la siembra.
"""
import math
from datetime import date
from statistics import mean

GRADIENTE_TERMICO_C_M = 0.0065  # −6,5 °C/km
SIGMA_MJ = 4.903e-9             # Stefan-Boltzmann, MJ K⁻⁴ m⁻² día⁻¹
CALOR_LATENTE_MJ_KG = 2.45      # 1 mm de agua evaporada = 2,45 MJ/m² (FAO-56)
UMBRAL_DIA_LLUVIA_MM = 1.0


def correccion_temperatura_c(elevacion_celda_m: float, elevacion_punto_m: float) -> float:
    """Grados que se suman a T de POWER: positivo si el punto está más bajo que la celda."""
    return (elevacion_celda_m - elevacion_punto_m) * GRADIENTE_TERMICO_C_M


def presion_atmosferica_kpa(z_m: float) -> float:
    return 101.3 * ((293 - 0.0065 * z_m) / 293) ** 5.26


def presion_vapor_saturacion_kpa(t_c: float) -> float:
    return 0.6108 * math.exp(17.27 * t_c / (t_c + 237.3))


def pendiente_curva_vapor_kpa_c(t_c: float) -> float:
    return 4098 * presion_vapor_saturacion_kpa(t_c) / (t_c + 237.3) ** 2


def radiacion_extraterrestre_mj(lat_grados: float, dia_del_anio: int) -> float:
    """Ra diaria (FAO-56, ecuación 21)."""
    phi = math.radians(lat_grados)
    dr = 1 + 0.033 * math.cos(2 * math.pi * dia_del_anio / 365)
    declinacion = 0.409 * math.sin(2 * math.pi * dia_del_anio / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(declinacion))))
    return (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(phi) * math.sin(declinacion) + math.cos(phi) * math.cos(declinacion) * math.sin(ws)
    )


def et0_penman_monteith_mm(
    tmax: float, tmin: float, rs: float, u2: float, ea: float, z_m: float, lat: float, dia_del_anio: int
) -> float:
    """ET0 diaria FAO-56 (ecuación 6) con G = 0. rs en MJ/m²/día, ea en kPa."""
    tmedia = (tmax + tmin) / 2
    es = (presion_vapor_saturacion_kpa(tmax) + presion_vapor_saturacion_kpa(tmin)) / 2
    delta = pendiente_curva_vapor_kpa_c(tmedia)
    gamma = 0.000665 * presion_atmosferica_kpa(z_m)

    ra = radiacion_extraterrestre_mj(lat, dia_del_anio)
    rso = (0.75 + 2e-5 * z_m) * ra
    relativa = min(rs / rso, 1.0) if rso > 0 else 1.0
    rns = 0.77 * rs
    rnl = (
        SIGMA_MJ * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2
        * (0.34 - 0.14 * math.sqrt(max(ea, 0.0)))
        * (1.35 * relativa - 0.35)
    )
    rn = rns - rnl

    numerador = 0.408 * delta * rn + gamma * 900 / (tmedia + 273) * u2 * max(es - ea, 0.0)
    return max(numerador / (delta + gamma * (1 + 0.34 * u2)), 0.0)


def et0_hargreaves_mm(tmax: float, tmin: float, lat: float, dia_del_anio: int) -> float:
    """FAO-56 ecuación 52. Solo necesita temperatura: cubre 1981-1983, cuando POWER no tiene radiación."""
    ra = radiacion_extraterrestre_mj(lat, dia_del_anio)
    return max(0.0023 * ((tmax + tmin) / 2 + 17.8) * math.sqrt(max(tmax - tmin, 0.0)) * 0.408 * ra, 0.0)


def _redondear(valor: float | None, decimales: int = 2) -> float | None:
    return None if valor is None else round(valor, decimales)


def agregar_derivadas(fila: dict, correccion_c: float | None, z_m: float, lat: float) -> None:
    """Agrega las columnas derived_* a una fila diaria que ya tiene power_*, smap_* e imerg_*."""
    ajuste = correccion_c or 0.0
    for nombre in ('t2m', 't2m_max', 't2m_min'):
        valor = fila.get(f'power_{nombre}')
        fila[f'derived_{nombre}_corr'] = _redondear(None if valor is None else valor + ajuste)

    tmax, tmin = fila['derived_t2m_max_corr'], fila['derived_t2m_min_corr']
    rs, u2, rocio = fila.get('power_allsky_sfc_sw_dwn'), fila.get('power_ws2m'), fila.get('power_t2mdew')
    dia = date.fromisoformat(fila['date']).timetuple().tm_yday

    # La presión de vapor real sale del punto de rocío de la celda, sin corregir por
    # elevación: en el valle la ET0 queda levemente sobrestimada (supuesto conservador).
    ea = None if rocio is None else presion_vapor_saturacion_kpa(rocio)
    pm = hg = vpd = None
    if None not in (tmax, tmin):
        hg = et0_hargreaves_mm(tmax, tmin, lat, dia)
        if ea is not None:
            es = (presion_vapor_saturacion_kpa(tmax) + presion_vapor_saturacion_kpa(tmin)) / 2
            vpd = max(es - ea, 0.0)
            if None not in (rs, u2):
                pm = et0_penman_monteith_mm(tmax, tmin, rs, u2, ea, z_m, lat, dia)

    fila['derived_vpd_kpa'] = _redondear(vpd, 3)
    fila['derived_et0_pm_mm'] = _redondear(pm)
    fila['derived_et0_hargreaves_mm'] = _redondear(hg)
    fila['derived_et0_mm'] = _redondear(pm if pm is not None else hg)
    fila['derived_et0_method'] = 'penman_monteith' if pm is not None else ('hargreaves' if hg is not None else None)

    # ET real modelada por MERRA-2: POWER la entrega como energía (MJ/m²/día)
    evptrns = fila.get('power_evptrns')
    fila['derived_evptrns_mm'] = _redondear(None if evptrns is None else evptrns / CALOR_LATENTE_MJ_KG)

    imerg, power = fila.get('imerg_precip_mm'), fila.get('power_prectotcorr')
    if imerg is not None:
        fila['derived_precip_mm'], fila['derived_precip_source'] = _redondear(imerg), 'imerg'
    elif power is not None:
        fila['derived_precip_mm'], fila['derived_precip_source'] = _redondear(power), 'power'
    else:
        fila['derived_precip_mm'], fila['derived_precip_source'] = None, None


def _dia_365(fecha: date) -> int:
    """Día del año en calendario de 365 días: el 29 de febrero cuenta como 28."""
    if fecha.month == 2 and fecha.day == 29:
        return 59
    return date(2001, fecha.month, fecha.day).timetuple().tm_yday


def percentil(valores_ordenados: list[float], q: float) -> float:
    posicion = (len(valores_ordenados) - 1) * q
    abajo = math.floor(posicion)
    arriba = min(abajo + 1, len(valores_ordenados) - 1)
    return valores_ordenados[abajo] + (valores_ordenados[arriba] - valores_ordenados[abajo]) * (posicion - abajo)


VARIABLES_CLIMATOLOGIA = [
    'derived_t2m_corr', 'derived_t2m_max_corr', 'derived_t2m_min_corr', 'power_prectotcorr',
    'power_rh2m', 'power_ws2m', 'power_allsky_sfc_sw_dwn', 'derived_et0_mm',
]


def climatologia_diaria(
    filas: list[dict],
    anio_inicio: int = 1991,
    anio_fin: int = 2020,
    ventana_dias: int = 15,
    variables: list[str] = VARIABLES_CLIMATOLOGIA,
    excluir_anio: int | None = None,
) -> list[dict]:
    """Media, p10 y p90 por día del año con una ventana móvil centrada.

    La lluvia usa POWER (serie continua desde 1981) y agrega la probabilidad de día
    de lluvia (> 1 mm). excluir_anio permite la climatología "dejando un año fuera"
    que exige el entrenamiento para no filtrar información.
    """
    por_dia: dict[int, dict[str, list[float]]] = {d: {v: [] for v in variables} for d in range(1, 366)}
    for fila in filas:
        fecha = date.fromisoformat(fila['date'])
        if not anio_inicio <= fecha.year <= anio_fin or fecha.year == excluir_anio:
            continue
        dia = _dia_365(fecha)
        for v in variables:
            if fila.get(v) is not None:
                por_dia[dia][v].append(fila[v])

    mitad = ventana_dias // 2
    salida = []
    for dia in range(1, 366):
        cercanos = [((dia - 1 + k) % 365) + 1 for k in range(-mitad, mitad + 1)]
        registro: dict = {'doy': dia}
        for v in variables:
            valores = sorted(x for d in cercanos for x in por_dia[d][v])
            if not valores:
                registro.update({f'{v}_mean': None, f'{v}_p10': None, f'{v}_p90': None})
                continue
            registro[f'{v}_mean'] = round(mean(valores), 2)
            registro[f'{v}_p10'] = round(percentil(valores, 0.1), 2)
            registro[f'{v}_p90'] = round(percentil(valores, 0.9), 2)
            if 'prectot' in v or 'precip' in v:
                registro[f'{v}_wet_day_prob'] = round(sum(x > UMBRAL_DIA_LLUVIA_MM for x in valores) / len(valores), 3)
        salida.append(registro)
    return salida
