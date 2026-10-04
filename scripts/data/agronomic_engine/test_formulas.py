import pytest

from formulas import (
  calculate_daily_depletion,
  calculate_gross_irrigation,
  calculate_initial_depletion,
  calculate_irrigation_interval,
  calculate_ks,
  calculate_raw,
  calculate_taw,
  calculate_theta_1500,
  calculate_theta_33,
  calculate_water_volume,
  should_irrigate,
)

def test_theta_1500_franco():
  result = calculate_theta_1500(
    sand=0.40,
    clay=0.20,
    organic_matter=2.5,
  )
  assert result == pytest.approx(0.137, abs=0.001)


def test_theta_33_franco():
  result = calculate_theta_33(
    sand=0.40,
    clay=0.20,
    organic_matter=2.5,
  )
  assert result == pytest.approx(0.280, abs=0.001)


def test_taw_franco_maiz():
  theta_1500 = calculate_theta_1500(0.40, 0.20, 2.5)
  theta_33 = calculate_theta_33(0.40, 0.20, 2.5)

  result = calculate_taw(
    theta_33=theta_33,
    theta_1500=theta_1500,
    zr=1.0,
    cfvo=0.0,
  )

  assert result == pytest.approx(142.59, abs=0.01)


def test_taw_franco_frijol():
  theta_1500 = calculate_theta_1500(0.40, 0.20, 2.5)
  theta_33 = calculate_theta_33(0.40, 0.20, 2.5)

  result = calculate_taw(
    theta_33=theta_33,
    theta_1500=theta_1500,
    zr=0.7,
    cfvo=0.0,
  )

  assert result == pytest.approx(99.81, abs=0.01)


def test_raw_frijol():
  taw = 99.81059545855999
  result = calculate_raw(taw, 0.45)
  assert result == pytest.approx(44.91, abs=0.01)


def test_irrigation_interval():
  result = calculate_irrigation_interval(
    raw=78.42,
    etc=5.0,
  )
  assert result == pytest.approx(15.684, abs=0.001)


def test_gross_irrigation():
  result = calculate_gross_irrigation(
    raw=78.0,
    efficiency=0.75,
  )
  assert result == pytest.approx(104.0)


def test_water_volume():
  result = calculate_water_volume(78.0)
  assert result == pytest.approx(780.0)


def test_initial_depletion():
  result = calculate_initial_depletion(
    theta_33=0.28,
    theta_smap=0.20,
    zr=0.7,
    taw=100.0,
  )
  assert result == pytest.approx(56.0)


def test_initial_depletion_is_clamped():
  result = calculate_initial_depletion(
    theta_33=0.28,
    theta_smap=0.05,
    zr=0.7,
    taw=50.0,
  )
  assert result == pytest.approx(50.0)


def test_daily_depletion():
  result = calculate_daily_depletion(
    previous_dr=56.0,
    effective_rainfall=5.0,
    irrigation=0.0,
    etc=5.0,
    taw=100.0,
  )
  assert result == pytest.approx(56.0)


def test_daily_depletion_is_clamped():
  result = calculate_daily_depletion(
    previous_dr=10.0,
    effective_rainfall=20.0,
    irrigation=0.0,
    etc=0.0,
    taw=100.0,
  )
  assert result == pytest.approx(0.0)


def test_should_irrigate():
  assert should_irrigate(45.0, 45.0) is True
  assert should_irrigate(44.9, 45.0) is False


def test_ks_without_stress():
  result = calculate_ks(
    dr=40.0,
    taw=100.0,
    p=0.45,
  )
  assert result == pytest.approx(1.0)


def test_ks_with_stress():
  result = calculate_ks(
    dr=70.0,
    taw=100.0,
    p=0.45,
  )
  assert result == pytest.approx(0.5454545, abs=0.000001)


def test_ks_at_wilting():
  result = calculate_ks(
    dr=100.0,
    taw=100.0,
    p=0.45,
  )
  assert result == pytest.approx(0.0)