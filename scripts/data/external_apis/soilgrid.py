import httpx

SOIL_GRID_URL = 'https://rest.isric.org/soilgrids/v2.0/properties/query'

SOIL_DEPTHS_AVAILABLE = [
  '0-5cm',
  '5-15cm',
  '15-30cm',
  '30-60cm',
  '60-100cm',
  '100-200cm',
]

SOIL_PROPERTIES = [
  'sand',
  'silt',
  'clay',
  'soc',
  'cfvo',
  'bdod',
  'phh2o',
  'cec',
  'nitrogen',
]

SOIL_STATISTICS = [
  'Q0.05',
  'Q0.5',
  'Q0.95',
]

async def execute(
  client: httpx.AsyncClient,
  lat: float,
  lon: float,
  depth: str = '60-100cm',
): 
  params = {
    'lon': lon,
    'lat': lat,
    'property': SOIL_PROPERTIES,
    'depth': depth,
    'value': SOIL_STATISTICS
  }

  if depth not in SOIL_DEPTHS_AVAILABLE:
    raise ValueError(
      f'Profundidad no válida: {depth}.',
      f'Valores permitidos: {', '.join(SOIL_DEPTHS_AVAILABLE)}'
    )
  
  response = await client.get(
    SOIL_GRID_URL,
    params=params
  )

  response.raise_for_status()
  return response.json()