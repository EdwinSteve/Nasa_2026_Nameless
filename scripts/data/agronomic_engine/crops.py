CROPS = {
  'maiz': {
    'name': 'Maíz',
    'zr': 1.0,
    'p': 0.55,
  },
  'sorgo': {
    'name': 'Sorgo',
    'zr': 1.0,
    'p': 0.55,
  },
  'soya': {
    'name': 'Soya',
    'zr': 0.9,
    'p': 0.50,
  },
  'frijol': {
    'name': 'Fríjol',
    'zr': 0.7,
    'p': 0.45,
  },
  'mani': {
    'name': 'Maní',
    'zr': 0.7,
    'p': 0.50,
  },
  'tomate': {
    'name': 'Tomate',
    'zr': 0.8,
    'p': 0.40,
  },
  'yuca': {
    'name': 'Yuca',
    'zr': 0.6,
    'p': 0.35,
  },
}

def get_crop(crop_id: str):
  try:
    return CROPS[crop_id]
  except KeyError:
    raise ValueError(
      f'Cultivo no encontrado: {crop_id}'
    )