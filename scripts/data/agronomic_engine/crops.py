from dataclasses import dataclass

@dataclass(frozen=True)
class Crop:
  id: str
  name: str
  zr: float
  p: float

CROPS = {
  "maiz": Crop(
    id="maiz",
    name="Maíz",
    zr=1.0,
    p=0.55,
  ),
  "sorgo": Crop(
    id="sorgo",
    name="Sorgo",
    zr=1.0,
    p=0.55,
  ),
  "soya": Crop(
    id="soya",
    name="Soya",
    zr=0.9,
    p=0.50,
  ),
  "frijol": Crop(
    id="frijol",
    name="Fríjol",
    zr=0.7,
    p=0.45,
  ),
  "mani": Crop(
    id="mani",
    name="Maní",
    zr=0.7,
    p=0.50,
  ),
  "tomate": Crop(
    id="tomate",
    name="Tomate",
    zr=0.8,
    p=0.40,
  ),
  "yuca": Crop(
    id="yuca",
    name="Yuca",
    zr=0.6,
    p=0.35,
  ),
}

def get_crop(crop_id: str) -> Crop:
    try:
        return CROPS[crop_id]
    except KeyError as exc:
        raise ValueError(f"Cultivo no encontrado: {crop_id}") from exc