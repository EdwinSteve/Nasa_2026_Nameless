# UPRA: aptitud de cultivos como filtro duro del motor

La UPRA (Unidad de Planificación Rural Agropecuaria) publica las zonificaciones de
aptitud de uso del suelo agropecuario: mapas que dicen, para cada zona del país, si un
cultivo tiene aptitud alta, media, baja o si no es apto. En Field Shift son un
**complemento local**: no reemplazan a los datos NASA, sirven para que el motor nunca
recomiende un cultivo que la UPRA marca como "No apto" en la ubicación de la finca, y
para sumar esa razón a la explicación (por ejemplo, "apto según UPRA + humedad SMAP
baja → frijol antes que maíz").

En el repo encaja junto a los filtros duros del catálogo que ya existen
(`filtros_duros` en `ml/surco_ml/predecir.py`, rama `feature/modelo-predictivo`), que
hoy descartan por altitud y pH.

## Servicio de aptitud del Huila (`huila_aptitud`)

| Campo | Valor |
|---|---|
| Nombre | Huila - Aptitud (zonificaciones por sistema productivo) |
| Servidor | ArcGIS Server 11.1 de la UPRA |
| Directorio REST | `https://geoservicios.upra.gov.co/arcgis/rest/services` |
| Servicio | `tipo_utilizacion_tierra/huila_aptitud/MapServer` |
| URL completa | `https://geoservicios.upra.gov.co/arcgis/rest/services/tipo_utilizacion_tierra/huila_aptitud/MapServer` |
| Tipo de capa | Feature Layer, geometría `esriGeometryPolygon` |
| Campo de visualización | `municipio` |
| Clases de aptitud | Aptitud Alta, Aptitud Media, Aptitud Baja, No Apta, Exclusiones legales |
| Portal de consulta | [SIPRA](https://sipra.upra.gov.co) (visor y descargas en shapefile) |
| Manual | [Manual SIPRA 2020](https://upra.gov.co/es-co/Documents/Manual_SIPRA_2020.pdf) |
| Licencia | Sin confirmar (ver [por verificar](#por-verificar)) |
| Estado al 2026-10-25 | **Caído**: responde `500 Service tipo_utilizacion_tierra/huila_aptitud/MapServer not started` |

El servidor organiza los servicios en 16 carpetas (`aptitud_uso_suelo`,
`ordenamiento_productivo`, `tipo_utilizacion_tierra`, `uso_suelo_rural`, etc.). Las
zonificaciones por departamento están en `tipo_utilizacion_tierra` con el patrón
`<departamento>_aptitud`: además del Huila existen `caldas_aptitud`,
`cundinamarca_aptitud`, `meta_aptitud`, `atlantico_aptitud`, `guaviare_aptitud` y
`providencia_aptitud`. Ojo: el listado público de esa carpeta aparece vacío
("Services: None"), así que los servicios se encuentran por su nombre, no navegando.

### Capas vistas en `huila_aptitud`

Leídas de la página `/MapServer/layers`. Los números de capa (`ID`) **no se vieron**:
la lista está en el orden de la página, no por ID.

| # en la página | Capa | Cultivo del catálogo (`cultivos.json`) |
|---|---|---|
| 1 | Huila - Aptitud Aguacate (*Persea americana* Miller) de variedad Hass | `aguacate_hass` |
| 2 | Huila - Aptitud Aguacate (*Persea americana* Miller) de variedad Lorena | ¿`aguacate_tropical`? (por verificar) |
| 3 | Huila - Aptitud Arroz (*Oryza sativa* L.) de riego (semestre 1 o 2) | `arroz_riego` |
| 4 | Huila - Aptitud especies nativas: Bocachico, Bagre rayado y Yamú | No aplica (piscicultura) |
| 5 | Huila - Aptitud Caña de azúcar (*Saccharum officinarum*) para la producción de panela | `cana_panelera` |
| 6+ | La página parecía seguir con más capas que no se alcanzaron a leer | — |

#### Implicaciones para las consultas

Según la [documentación oficial de la API REST](https://geoservicios.upra.gov.co/arcgis/sdk/rest/index.html)
que trae el propio servidor de la UPRA (ArcGIS Server 11.1), hay dos operaciones útiles:

- **`identify` sobre el servicio completo (la recomendada).** Una sola petición por
  finca devuelve la clase de aptitud de **todas** las capas en ese punto, sin conocer
  los números de capa:
  `.../huila_aptitud/MapServer/identify?geometry=<lon>,<lat>&geometryType=esriGeometryPoint&sr=4326&layers=all&tolerance=0&mapExtent=<lon-0.01>,<lat-0.01>,<lon+0.01>,<lat+0.01>&imageDisplay=400,400,96&returnGeometry=false&returnFieldName=true&returnUnformattedValues=true&f=json`.
  `tolerance`, `mapExtent` e `imageDisplay` son obligatorios aunque no haya mapa en
  pantalla; con `tolerance=0` solo cuenta el polígono que contiene el punto. Cada
  resultado trae `layerId`, `layerName` y `attributes`, así que de paso salen los IDs
  de capa y los nombres de campo que hoy están en "por verificar". Con 4 fincas demo
  son 4 peticiones; el resultado se precalcula en `data/` para que el motor no dependa
  de que el servicio esté arriba.
- **`query` por capa (alternativa o para validar).**
  `.../MapServer/<ID>/query?geometry=<lon>,<lat>&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false&f=json`.
  Sirve si `identify` no está habilitado. También acepta `f=geojson` y, si algún día se
  quieren bajar los polígonos del Huila, paginar con `resultOffset` y
  `resultRecordCount` mientras la respuesta traiga `exceededTransferLimit: true` (el
  tope por petición es el `maxRecordCount` de la capa).
- Con `returnFieldName=true` y `returnUnformattedValues=true` el `identify` devuelve el
  nombre real del campo (no el alias) y el **código** del dominio en vez de la etiqueta.
  Guardar los dos (código y etiqueta) para que la explicación del motor diga
  "No apta" y no un número.
- Pasar siempre la referencia espacial de entrada (`sr=4326` en `identify`, `inSR=4326`
  en `query`): las fincas están en lat/lon y el sistema de referencia de las capas no
  se ha confirmado.
- Si un cultivo **no tiene capa**, el filtro no debe descartarlo: "sin zonificación
  UPRA" es distinto de "No apto".
- "Exclusiones legales" (por ejemplo, áreas protegidas) también debería descartar el
  cultivo, pero con un motivo distinto a "No apto" en la explicación.
- Una consulta que no devuelve polígonos puede significar que la finca cae fuera de la
  frontera agrícola o en un hueco de la capa; tratarlo como "sin dato", no como "apto".
- La frontera agrícola nacional está en otro servicio:
  `ordenamiento_productivo/frontera_agricola_frontera_agricola_condicionada/MapServer`.

### Por verificar

Cosas que no se pudieron confirmar porque el servicio estaba caído o porque solo se vio
la página HTML:

- **Servicio caído.** El 2026-10-25 tanto `huila_aptitud` como `cundinamarca_aptitud`
  respondían "Service not started". Volver a probar antes de construir sobre él; si
  sigue caído, la alternativa es descargar los shapefiles desde SIPRA.
- **Números de capa (`ID`)** de cada cultivo. Salen de `.../MapServer?f=pjson` (arreglo
  `layers`) o de los `layerId` de un `identify`.
- **Nombre y valores del campo de aptitud.** No se vio la lista de campos. El manual
  SIPRA habla de A1 (alta), A2 (media), A3 (baja) y N1 (no apto), y la descripción de
  la capa usa los textos "Aptitud Alta ... No Apta, Exclusiones legales". Hay que ver
  en `.../MapServer/<ID>?f=pjson` (`fields` y `drawingInfo.renderer`) cuál de las dos
  formas viene en los datos.
- **Sistema de referencia** (`spatialReference.wkid`) y extensión de las capas.
- **Lista completa de capas.** No se vieron maíz, frijol ni café para el Huila, que son
  cultivos de las fincas demo (`villavieja-seco`, `garzon-cafe`, `pitalito-cafe`). Si no
  existen, el filtro UPRA solo afecta a la finca de Campoalegre (arroz) y a los
  cultivos de la tabla de arriba.
- **Aguacate Lorena ↔ `aguacate_tropical`**: confirmar que Lorena es una variedad
  antillana/tropical antes de usar esa capa para ese cultivo.
- **Descripción repetida.** Todas las capas traen la misma descripción, que habla de
  ganadería de leche con pastos y no del cultivo de la capa. Parece un error de
  metadatos de la UPRA; no usarla como fuente de la metodología.
- **Licencia y atribución.** No se encontró en el servicio. Revisar SIPRA o los
  términos de uso de upra.gov.co.
- **Escala y fecha** de cada zonificación (la página `/MapServer/<ID>/metadata` debería
  tenerlas).

### Avisos de calidad

1. **Escala.** Las zonificaciones de la UPRA son de planificación departamental o
   nacional (escala gruesa). Una finca pequeña puede caer en el borde de dos clases;
   el filtro debe mostrar la clase como referencia, no como diagnóstico de la finca.
2. **No es un dato satelital NASA.** En la explicación hay que nombrarlo aparte de los
   valores NASA ("según la UPRA ...") para que quede claro qué parte viene de cada
   fuente.
3. **Las capas cambian.** La Gobernación del Huila y la UPRA han ajustado los mapas de
   aptitud del departamento; guardar con el resultado precalculado la fecha de consulta
   y el nombre exacto de la capa.
4. **Red.** Desde el entorno en la nube de Claude, `upra.gov.co` está bloqueado por la
   política de red; los scripts de descarga tienen que correr en una máquina del equipo.

### Atribución

Propuesta hasta confirmar la licencia:

> Zonificación de aptitud: Unidad de Planificación Rural Agropecuaria (UPRA), SIPRA, servicio `huila_aptitud` (consultado el AAAA-MM-DD).

---
