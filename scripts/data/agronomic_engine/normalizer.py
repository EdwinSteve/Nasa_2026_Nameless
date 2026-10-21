"""
Suelo del esquema 2.0 de datos_tierra -> entradas del motor.

Desde el esquema 2.0 (ml/datos_tierra) `soil` ya llega en unidades
convencionales, así que aquí ya no se divide por los factores (d_factor)
de SoilGrids:
- sand/silt/clay: %             -> fracción 0-1 dividiendo entre 100.
- soc: g/kg                     -> MO en % (ver abajo).
- cfvo: vol% (cm³/100 cm³)      -> se usa tal cual: calculate_taw espera %.
- bdod kg/dm³, phh2o pH, cec cmol(c)/kg, nitrogen g/kg y wv* m³/m³
  ya están en las unidades del modelo.

Para Saxton & Rawls:
- S y C se expresan como fracciones 0-1.
- MO se expresa en %.

SoilGrids proporciona SOC, no materia orgánica (MO). La conversión
SOC -> MO usa el factor 1.724 (van Bemmelen), el mismo de
ml/datos_tierra/suelo.py:
MO (%) = SOC (g/kg) / 10 * 1.724
Es una hipótesis del modelo y debe poder sustituirse por un valor de
laboratorio cuando esté disponible.

Cada propiedad se promedia por espesor desde la superficie hasta la
profundidad de raíz del cultivo (Zr), con la mediana Q0.5 de SoilGrids.
"""

from validations import validate_positive

SCHEMA_VERSION = "2.0"
SOC_TO_MO_FACTOR = 1.724
DEFAULT_STAT = "Q0.5"
ENGINE_PROPERTIES = ("sand", "clay", "soc", "cfvo")


def percent_to_fraction(value: float) -> float:
  """% -> fracción 0-1."""
  return value / 100.0


def soc_to_organic_matter(soc_g_kg: float) -> float:
  """SOC en g/kg -> MO en %."""
  return soc_g_kg / 10.0 * SOC_TO_MO_FACTOR


def weighted_to_depth(
  layers: dict,
  prop: str,
  depth_m: float,
  stat: str = DEFAULT_STAT,
) -> float | None:
  """
  Promedio ponderado por espesor de `prop` desde 0 hasta depth_m.

  `layers` es soil.layers del esquema 2.0:
  {'0-5cm': {'top_cm': 0, 'bottom_cm': 5, 'properties': {'sand': {'Q0.5': 40.1}}}}

  Las capas sin dato no cuentan en el promedio. Si ninguna tiene dato
  devuelve None.
  """
  validate_positive(depth_m, "La profundidad")
  depth_cm = depth_m * 100.0
  total = weight = 0.0

  for layer in layers.values():
    thickness = max(0.0, min(layer["bottom_cm"], depth_cm) - layer["top_cm"])
    value = layer["properties"].get(prop, {}).get(stat)
    if thickness and value is not None:
      total += value * thickness
      weight += thickness

  return total / weight if weight else None


def engine_soil_inputs(
  data: dict,
  zr: float,
  stat: str = DEFAULT_STAT,
) -> dict:
  """
  JSON de datos_tierra (esquema 2.0) -> argumentos de suelo del motor.

  Devuelve sand, clay, organic_matter y cfvo, listos para
  calculate_crop_water_requirements(**engine_soil_inputs(data, crop.zr), ...).
  """
  version = data.get("schema_version")
  if version != SCHEMA_VERSION:
    raise ValueError(
      f"Se esperaba el esquema {SCHEMA_VERSION} de datos_tierra y llegó {version}. "
      "En el esquema 1.0 el suelo venía en unidades crudas de SoilGrids."
    )

  soil = data.get("soil")
  if soil is None:
    status = data.get("sources", {}).get("soilgrids", {}).get("status", "no pedida")
    raise ValueError(
      f"El lote no tiene datos de suelo: SoilGrids no respondió (estado: {status})."
    )
  if soil.get("empty"):
    raise ValueError(
      "El lote no tiene datos de suelo: SoilGrids devuelve vacío en zonas "
      "urbanas y cuerpos de agua."
    )

  values = {
    prop: weighted_to_depth(soil["layers"], prop, zr, stat)
    for prop in ENGINE_PROPERTIES
  }
  missing = [prop for prop, value in values.items() if value is None]
  if missing:
    raise ValueError(f"Faltan propiedades de suelo hasta {zr} m: {', '.join(missing)}.")

  return {
    "sand": percent_to_fraction(values["sand"]),
    "clay": percent_to_fraction(values["clay"]),
    "organic_matter": soc_to_organic_matter(values["soc"]),
    "cfvo": values["cfvo"],
  }
