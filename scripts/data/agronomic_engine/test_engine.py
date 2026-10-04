import pytest
from pprint import pprint 

from engine import (
  calculate_crop_water_requirements,
  calculate_daily_state
)

def test_engine_frijol():
  result = calculate_crop_water_requirements(
    crop_id="frijol",
    sand=0.40,
    clay=0.20,
    organic_matter=2.5,
    cfvo=0.0,
    etc=5.0,
    theta_smap=0.20,
    irrigation_efficiency=0.90,
  )

  pprint(result)

  assert result["crop"] == "Fríjol"
  assert result["zr_m"] == pytest.approx(0.7)
  assert result["taw_mm"] == pytest.approx(99.81, abs=0.01)
  assert result["raw_mm"] == pytest.approx(44.91, abs=0.01)
  assert result["initial_depletion_mm"] == pytest.approx(55.72711545856, abs=0.000001)
  assert result["should_irrigate"] is True
  assert result["ks"] == pytest.approx(0.804, abs=0.001)


def test_daily_state():
  result = calculate_daily_state(
    previous_dr=40.0,
    effective_rainfall=0.0,
    irrigation=0.0,
    etc=5.0,
    taw=100.0,
    p=0.45,
  )

  pprint(result)

  assert result["depletion_mm"] == pytest.approx(45.0)
  assert result["should_irrigate"] is True
  assert result["ks"] == pytest.approx(1.0)