import httpx

NASA_POWER_URL = 'https://power.larc.nasa.gov/api/temporal/daily/point'

POWER_PARAMETERS = [
  'T2M_MAX',
  'T2M_MIN',
  'PRECTOTCORR',
  'RH2M',
  'WS2M',
  'ALLSKY_SFC_SW_DWN',
  'GWETROOT',
]

async def execute(
  client: httpx.AsyncClient,
  lat: float,
  lon: float,
  start_date: str,
  end_date: str,
):
  params = {
    'parameters': ','.join(POWER_PARAMETERS),
    'community': 'AG',
    'longitude': lon,
    'latitude': lat,
    'start': start_date,
    'end': end_date,
    'format': 'JSON',
  }

  response = await client.get(
    NASA_POWER_URL,
    params=params
  )

  response.raise_for_status()
  return response.json()