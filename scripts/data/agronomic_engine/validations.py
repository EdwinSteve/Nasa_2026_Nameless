def validate_fraction(value: float, name: str) -> None:
  if not 0.0 <= value <= 1.0:
    raise ValueError(f"{name} debe estar entre 0 y 1.")


def validate_percentage(value: float, name: str) -> None:
  if not 0.0 <= value <= 100.0:
    raise ValueError(f"{name} debe estar entre 0 y 100.")


def validate_positive(value: float, name: str) -> None:
  if value <= 0:
    raise ValueError(f"{name} debe ser mayor que 0.")


def validate_efficiency(efficiency: float) -> None:
  validate_fraction(efficiency, "La eficiencia")


def validate_crop_parameters(zr: float, p: float) -> None:
  validate_positive(zr, "Zr")
  if not 0.0 < p < 1.0:
    raise ValueError("p debe estar entre 0 y 1, sin incluir los extremos.")