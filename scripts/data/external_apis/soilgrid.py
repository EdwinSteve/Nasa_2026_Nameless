import asyncio

import httpx


RETRYABLE_STATUS = (429, 500, 502, 503, 504)

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
  statistics: list[str] | None = None,
  retries: int = 3,
): 
  
  depths = [depth] if isinstance(depth, str) else list(depth)
  invalid = [d for d in depths if d not in SOIL_DEPTHS_AVAILABLE]
  if invalid:
    raise ValueError(
      f"Profundidad no válida: {invalid}. "
      f"Valores permitidos: {', '.join(SOIL_DEPTHS_AVAILABLE)}"
    )

  params = {
    'lon': lon,
    'lat': lat,
    'property': SOIL_PROPERTIES,
    'depth': depth,
    'value': statistics or SOIL_STATISTICS
  }

  for attempt in range(1, retries + 1):
    try:
      response = await client.get(SOIL_GRID_URL, params=params)
      response.raise_for_status()
      return response.json()
    except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
      retryable = isinstance(exc, httpx.TimeoutException) or (
        exc.response.status_code in RETRYABLE_STATUS
      )
      if not retryable or attempt == retries:
        raise
      await asyncio.sleep(10 * attempt)  # 10 s, 20 s