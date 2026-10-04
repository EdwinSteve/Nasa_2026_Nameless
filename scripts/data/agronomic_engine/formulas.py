from validations import (
  validate_efficiency,
  validate_fraction,
  validate_percentage,
  validate_positive
)

# Capacidad de marchitez 
def calculate_theta_1500(
  sand: float,
  clay: float,
  organic_matter: float,
) -> float:
  """
  4.9 - Humedad al punto de marchitez permanente (Saxton & Rawls, 2006).

  sand y clay: fracciones 0-1.
  organic_matter: porcentaje.
  """
  validate_fraction(sand, "Arena")
  validate_fraction(clay, "Arcilla")
  validate_percentage(organic_matter, "Materia orgánica")

  theta_1500t = (
    -0.024 * sand
    + 0.487 * clay
    + 0.006 * organic_matter
    + 0.005 * (sand * organic_matter)
    - 0.013 * (clay * organic_matter)
    + 0.068 * (sand * clay)
    + 0.031
  )

  return theta_1500t + (0.14 * theta_1500t - 0.02)

# Capacidad de campo
def calculate_theta_33(
  sand: float,
  clay: float,
  organic_matter: float,
) -> float:
  """
  4.9 - Humedad a capacidad de campo (Saxton & Rawls, 2006).

  sand y clay: fracciones 0-1.
  organic_matter: porcentaje.
  """
  validate_fraction(sand, "Arena")
  validate_fraction(clay, "Arcilla")
  validate_percentage(organic_matter, "Materia orgánica")

  theta_33t = (
    -0.251 * sand
    + 0.195 * clay
    + 0.011 * organic_matter
    + 0.006 * (sand * organic_matter)
    - 0.027 * (clay * organic_matter)
    + 0.452 * (sand * clay)
    + 0.299
  )

  return theta_33t + (
    1.283 * theta_33t**2
    - 0.374 * theta_33t
    - 0.015
  )

def calculate_taw(
  theta_33: float,
  theta_1500: float,
  zr: float,
  cfvo: float = 0.0,
) -> float:
  """4.10 - Agua total disponible (mm)."""
  validate_positive(zr, "Zr")
  validate_percentage(cfvo, "CFVO")

  if theta_33 < theta_1500:
    raise ValueError("theta_33 no puede ser menor que theta_1500.")

  taw = (
    1000.0
    * (theta_33 - theta_1500)
    * zr
    * (1.0 - cfvo / 100.0)
  )

  return max(taw, 0.0)

def calculate_raw(taw: float, p: float) -> float:
  """4.11 - Agua fácilmente aprovechable (mm)."""
  if taw < 0:
    raise ValueError("TAW no puede ser negativo.")
  if not 0.0 < p < 1.0:
    raise ValueError("p debe estar entre 0 y 1.")
  return p * taw

def calculate_irrigation_interval(raw: float, etc: float) -> float:
  """4.12 - Intervalo teórico entre riegos (días)."""
  if raw < 0:
    raise ValueError("RAW no puede ser negativo.")
  validate_positive(etc, "ETc")
  return raw / etc


def calculate_net_irrigation(raw: float) -> float:
  """4.12 - Lámina neta (mm)."""
  if raw < 0:
    raise ValueError("RAW no puede ser negativo.")
  return raw


def calculate_gross_irrigation(
  raw: float,
  efficiency: float,
) -> float:
  """4.12 - Lámina bruta (mm)."""
  if raw < 0:
    raise ValueError("RAW no puede ser negativo.")
  validate_efficiency(efficiency)
  return raw / efficiency


def calculate_water_volume(
  irrigation_depth: float,
) -> float:
  """4.12 - Volumen de agua en m³/ha."""
  if irrigation_depth < 0:
    raise ValueError("La lámina no puede ser negativa.")
  return irrigation_depth * 10.0

def calculate_initial_depletion(
  theta_33: float,
  theta_smap: float,
  zr: float,
  taw: float,
) -> float:
  """4.13 - Agotamiento inicial Dr,0 (mm), acotado entre 0 y TAW."""
  validate_positive(zr, "Zr")

  if taw < 0:
    raise ValueError("TAW no puede ser negativo.")

  dr_initial = 1000.0 * (theta_33 - theta_smap) * zr

  return max(0.0, min(dr_initial, taw))

def calculate_daily_depletion(
  previous_dr: float,
  effective_rainfall: float,
  irrigation: float,
  etc: float,
  taw: float,
) -> float:
  """4.14 - Balance hídrico diario, acotado entre 0 y TAW."""
  if taw < 0:
    raise ValueError("TAW no puede ser negativo.")
  if previous_dr < 0:
    raise ValueError("Dr anterior no puede ser negativo.")
  if effective_rainfall < 0:
    raise ValueError("La lluvia efectiva no puede ser negativa.")
  if irrigation < 0:
    raise ValueError("El riego no puede ser negativo.")
  if etc < 0:
    raise ValueError("ETc no puede ser negativa.")

  dr = (
    previous_dr
    - effective_rainfall
    - irrigation
    + etc
  )

  return max(0.0, min(dr, taw))


def should_irrigate(dr: float, raw: float) -> bool:
  """4.14 - Indica si el agotamiento alcanzó el umbral de riego."""
  if dr < 0:
    raise ValueError("Dr no puede ser negativo.")
  if raw < 0:
    raise ValueError("RAW no puede ser negativo.")

  return dr >= raw

def calculate_ks(
  dr: float,
  taw: float,
  p: float,
) -> float:
  """
  4.15 - Coeficiente de estrés hídrico.

  Ks = 1 si Dr <= RAW.
  Ks = (TAW - Dr) / ((1-p) * TAW) si Dr > RAW.
  """
  if taw <= 0:
    raise ValueError("TAW debe ser mayor que 0.")
  if not 0.0 < p < 1.0:
    raise ValueError("p debe estar entre 0 y 1.")
  if not 0.0 <= dr <= taw:
    raise ValueError("Dr debe estar entre 0 y TAW.")

  raw = p * taw

  if dr <= raw:
    return 1.0

  ks = (taw - dr) / ((1.0 - p) * taw)

  return max(0.0, min(ks, 1.0))