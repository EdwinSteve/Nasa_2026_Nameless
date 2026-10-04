from crops import get_crop
from formulas import (
  calculate_daily_depletion,
  calculate_gross_irrigation,
  calculate_initial_depletion,
  calculate_irrigation_interval,
  calculate_ks,
  calculate_net_irrigation,
  calculate_raw,
  calculate_taw,
  calculate_theta_1500,
  calculate_theta_33,
  calculate_water_volume,
  should_irrigate,
)

def calculate_crop_water_requirements(
  crop_id: str,
  sand: float,
  clay: float,
  organic_matter: float,
  cfvo: float,
  etc: float,
  theta_smap: float,
  irrigation_efficiency: float,
):
  """
  Ejecuta los apartados 4.9 a 4.15 para un estado inicial.

  ETc y theta_smap deben venir de las capas/servicios externos
  correspondientes (por ejemplo NASA POWER + cálculo ET0/ETc y SMAP).
  """
  crop = get_crop(crop_id)

  theta_1500 = calculate_theta_1500(
    sand=sand,
    clay=clay,
    organic_matter=organic_matter,
  )

  theta_33 = calculate_theta_33(
    sand=sand,
    clay=clay,
    organic_matter=organic_matter,
  )

  taw = calculate_taw(
    theta_33=theta_33,
    theta_1500=theta_1500,
    zr=crop.zr,
    cfvo=cfvo,
  )

  raw = calculate_raw(
    taw=taw,
    p=crop.p,
  )

  interval = calculate_irrigation_interval(
    raw=raw,
    etc=etc,
  )

  net_irrigation = calculate_net_irrigation(raw)

  gross_irrigation = calculate_gross_irrigation(
    raw=raw,
    efficiency=irrigation_efficiency,
  )

  volume = calculate_water_volume(net_irrigation)

  dr_initial = calculate_initial_depletion(
    theta_33=theta_33,
    theta_smap=theta_smap,
    zr=crop.zr,
    taw=taw,
  )

  irrigate = should_irrigate(
    dr=dr_initial,
    raw=raw,
  )

  ks = calculate_ks(
    dr=dr_initial,
    taw=taw,
    p=crop.p,
  )

  return {
    "crop": crop.name,
    "crop_id": crop.id,
    "zr_m": crop.zr,
    "p": crop.p,
    "theta_1500": theta_1500,
    "theta_33": theta_33,
    "taw_mm": taw,
    "raw_mm": raw,
    "irrigation_interval_days": interval,
    "net_irrigation_mm": net_irrigation,
    "gross_irrigation_mm": gross_irrigation,
    "water_volume_m3_ha": volume,
    "initial_depletion_mm": dr_initial,
    "should_irrigate": irrigate,
    "ks": ks,
  }


def calculate_daily_state(
  previous_dr: float,
  effective_rainfall: float,
  irrigation: float,
  etc: float,
  taw: float,
  p: float,
):
  """Actualiza el estado diario y calcula riego y estrés."""
  dr = calculate_daily_depletion(
    previous_dr=previous_dr,
    effective_rainfall=effective_rainfall,
    irrigation=irrigation,
    etc=etc,
    taw=taw,
  )

  return {
    "depletion_mm": dr,
    "should_irrigate": should_irrigate(
      dr=dr,
      raw=p * taw,
    ),
    "ks": calculate_ks(
      dr=dr,
      taw=taw,
      p=p,
    ),
  }