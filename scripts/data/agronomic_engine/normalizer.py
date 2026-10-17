"""
Conversión de unidades de SoilGrids.

Las conversiones se basan en la documentación oficial de SoilGrids:
- sand/silt/clay: g/kg -> % dividiendo entre 10.
- soc: dg/kg -> g/kg dividiendo entre 10.
- cfvo: vol‰ -> vol% dividiendo entre 10.
- bdod: cg/cm³ -> kg/dm³ dividiendo entre 100.
- phh2o: pH x 10 -> pH dividiendo entre 10.
- cec: mmol(c)/kg -> cmol(c)/kg dividiendo entre 10.
- nitrogen: cg/kg -> g/kg dividiendo entre 100.

Para Saxton & Rawls:
- S y C se expresan como fracciones 0-1.
- MO se expresa en %.

SoilGrids proporciona SOC, no materia orgánica (MO). La conversión
SOC -> MO usa el factor 1.724 como aproximación explícita:
MO (%) = SOC (g/kg) / 10 * 1.724
Es una hipótesis del modelo y debe poder sustituirse por un valor de
laboratorio cuando esté disponible.
"""

def soilgrids_fraction(value: float) -> float:
  """g/kg -> fracción 0-1."""
  return value / 1000.0


def soilgrids_percent(value: float) -> float:
  """g/kg -> porcentaje."""
  return value / 10.0


def soilgrids_soc_to_mo(value: float) -> float:
  """
  SOC SoilGrids en dg/kg -> MO en %.

  Se aplica:
      SOC (g/kg) = valor / 10
      MO (%) = SOC (g/kg) * 1.724 / 10
  """
  soc_g_kg = value / 10.0
  soc_percent = soc_g_kg / 10.0
  return soc_percent * 1.724


def soilgrids_cfvo_percent(value: float) -> float:
  """vol‰ -> vol%."""
  return value / 10.0


def soilgrids_bdod_kg_dm3(value: float) -> float:
  """cg/cm³ -> kg/dm³."""
  return value / 100.0


def soilgrids_ph(value: float) -> float:
  """pH x 10 -> pH."""
  return value / 10.0


def soilgrids_cec_cmol_kg(value: float) -> float:
  """mmol(c)/kg -> cmol(c)/kg."""
  return value / 10.0


def soilgrids_nitrogen_g_kg(value: float) -> float:
  """cg/kg -> g/kg."""
  return value / 100.0