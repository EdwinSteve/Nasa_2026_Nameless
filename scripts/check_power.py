import httpx

p = ['T2M_MAX', 'T2M_MIN', 'RH2M', 'WS2M', 'ALLSKY_SFC_SW_DWN', 'PRECTOTCORR']
r = httpx.get(
  'https://power.larc.nasa.gov/api/temporal/daily/point',
  params={'parameters': ','.join(p), 'community': 'AG', 'latitude': 3.22,
          'longitude': -75.22, 'start': '20260801', 'end': '20261005', 'format': 'JSON'},
  timeout=120,
).json()
for k, v in r['properties']['parameter'].items():
  ok = [d for d, x in sorted(v.items()) if x != -999.0]
  print(k, ok[-1] if ok else None)