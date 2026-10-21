import pytest

from engine import calculate_crop_water_requirements
from normalizer import (
  engine_soil_inputs,
  soc_to_organic_matter,
  weighted_to_depth,
)

DEPTHS_CM = ((0, 5), (5, 15), (15, 30), (30, 60), (60, 100), (100, 200))


def _soil(**values_by_prop):
  """soil del esquema 2.0 con un valor Q0.5 por capa para cada propiedad."""
  layers = {}
  for i, (top, bottom) in enumerate(DEPTHS_CM):
    layers[f"{top}-{bottom}cm"] = {
      "top_cm": top,
      "bottom_cm": bottom,
      "properties": {
        prop: {"mean": values[i], "Q0.5": values[i]}
        for prop, values in values_by_prop.items()
      },
    }
  return {"empty": False, "layers": layers}


def _uniform(**values):
  return _soil(**{prop: [value] * len(DEPTHS_CM) for prop, value in values.items()})


def test_weighted_to_depth_cuts_the_layer_at_zr():
  soil = _soil(sand=[50, 40, 40, 30, 20, 10])

  # 0,7 m: 5·50 + 10·40 + 15·40 + 30·30 + 10·20 (solo 10 de los 40 cm de 60-100)
  assert weighted_to_depth(soil["layers"], "sand", 0.7) == pytest.approx(2350 / 70)


def test_weighted_to_depth_skips_missing_layers():
  soil = _soil(clay=[None, 20, 30, None, None, None])

  assert weighted_to_depth(soil["layers"], "clay", 0.3) == pytest.approx((10 * 20 + 15 * 30) / 25)
  assert weighted_to_depth(soil["layers"], "silt", 0.3) is None


def test_soc_to_organic_matter():
  assert soc_to_organic_matter(14.5) == pytest.approx(2.4998)


def test_engine_soil_inputs_converts_units():
  data = {"schema_version": "2.0", "soil": _uniform(sand=40.0, clay=20.0, soc=14.5, cfvo=8.0)}

  assert engine_soil_inputs(data, zr=0.7) == pytest.approx({
    "sand": 0.40,
    "clay": 0.20,
    "organic_matter": 2.4998,
    "cfvo": 8.0,
  })


def test_engine_soil_inputs_feeds_the_engine():
  # El mismo suelo de test_engine_frijol, pero llegando como JSON 2.0
  soc_for_mo_2_5 = 2.5 * 10 / 1.724
  data = {"schema_version": "2.0", "soil": _uniform(sand=40.0, clay=20.0, soc=soc_for_mo_2_5, cfvo=0.0)}

  result = calculate_crop_water_requirements(
    crop_id="frijol",
    **engine_soil_inputs(data, zr=0.7),
    etc=5.0,
    theta_smap=0.20,
    irrigation_efficiency=0.90,
  )

  assert result["taw_mm"] == pytest.approx(99.81, abs=0.01)
  assert result["raw_mm"] == pytest.approx(44.91, abs=0.01)


def test_rejects_schema_1():
  with pytest.raises(ValueError, match="esquema 2.0"):
    engine_soil_inputs({"schema_version": "1.0", "soil": _uniform(sand=40.0)}, zr=0.7)


def test_rejects_empty_soil():
  with pytest.raises(ValueError, match="zonas urbanas"):
    engine_soil_inputs({"schema_version": "2.0", "soil": {"empty": True, "layers": {}}}, zr=0.7)


def test_rejects_soil_when_soilgrids_failed():
  data = {"schema_version": "2.0", "soil": None, "sources": {"soilgrids": {"status": "error"}}}

  with pytest.raises(ValueError, match="no respondió \\(estado: error\\)"):
    engine_soil_inputs(data, zr=0.7)


def test_reports_missing_properties():
  data = {"schema_version": "2.0", "soil": _uniform(sand=40.0, clay=20.0)}

  with pytest.raises(ValueError, match="soc, cfvo"):
    engine_soil_inputs(data, zr=0.7)
