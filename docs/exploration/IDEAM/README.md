# IDEAM: estaciones en tierra para validar los datos NASA

El IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales) publica en
[datos.gov.co](https://www.datos.gov.co) los datos de su red de estaciones automáticas.
En Field Shift son un **complemento local**: no reemplazan a NASA POWER ni a GPM IMERG,
sirven para comprobar qué tan bien representan esos productos satelitales la lluvia
real del Huila.

## Dataset de precipitación (`s54a-sgyg`)

| Campo | Valor |
|---|---|
| Nombre | Precipitación |
| Identificador | `s54a-sgyg` |
| Portal | https://www.datos.gov.co/d/s54a-sgyg |
| API (Socrata) | `https://www.datos.gov.co/resource/s54a-sgyg.json` |
| Fuente y atribución | Instituto de Hidrología, Meteorología y Estudios Ambientales - IDEAM, Bogotá D.C. ([ideam.gov.co](http://www.ideam.gov.co)) |
| Categoría | Ambiente y Desarrollo Sostenible |
| Procedencia | Oficial |
| Licencia | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.es) |
| Publicado | 2019-08-27 |
| Última actualización de filas | 2026-10-25 (se actualiza de forma continua) |
| Resolución temporal | Lluvia acumulada cada 10 minutos |
| Cobertura | Estaciones meteorológicas automáticas en todo el territorio colombiano |

### Descripción

Cantidad de lluvia registrada cada 10 minutos en estaciones meteorológicas del país.
Los datos pasaron un control de calidad básico según las recomendaciones de la
Organización Meteorológica Mundial (OMM): se corrigieron o eliminaron valores que no
cumplían esos controles. Según el IDEAM, el conjunto sirve para analizar el
comportamiento de la precipitación, identificar eventos extremos, hacer estudios
climáticos e hidrológicos y apoyar sistemas de alerta temprana.

### Columnas

Cada fila es una lectura de 10 minutos de una estación. Las cifras de la columna "Notas"
salen de las estadísticas que el portal guarda en caché (`cachedContents`), no de una
consulta nuestra: son aproximadas y pueden estar desactualizadas (ver
[por verificar](#por-verificar)).

| Campo (`fieldName`) | Tipo | Descripción | Notas |
|---|---|---|---|
| `codigoestacion` | text | Identificador de la estación en el catálogo del IDEAM | 800 valores distintos. Es **texto con ceros a la izquierda** (`0021209920`): no convertir a número. Es la llave para unir con otras tablas del IDEAM. |
| `codigosensor` | text | Código del sensor | Constante: `0240` (precipitación). |
| `fechaobservacion` | calendar_date | Fecha y hora de la medición | Fecha-hora sin zona horaria (`2019-09-02T11:00:00.000`), en pasos de 10 min. Rango en caché: 2003-01-20 a 2022-04-26. |
| `valorobservado` | number | Valor medido | Lluvia en mm acumulada en la lectura. ~95 % de las lecturas valen 0. Máximo en caché: 30 mm en 10 min. |
| `nombreestacion` | text | Nombre de la estación | 783 valores distintos (menos que códigos: hay nombres repetidos o estaciones renombradas). Formato `NOMBRE - AUT`. |
| `departamento` | text | Departamento donde está la estación | 41 valores. HUILA tiene ~9,1 M de filas. Mayúsculas, pero **con tildes en algunos** (`BOYACÁ`, `CHOCÓ`, `NARIÑO`, `QUINDÍO`, `CÓRDOBA`); `HUILA` va sin tilde. Bogotá aparece de dos formas (`BOGOTA D.C.` y `BOGOTA`). |
| `municipio` | text | Municipio donde está la estación | 473 valores, también con tildes (`SAN AGUSTÍN`). En el Huila destacan `NEIVA` y `SAN AGUSTÍN` con más de 1 M de filas cada uno. |
| `zonahidrografica` | text | Zona hidrográfica de la estación | 33 valores. La mayor parte del Huila cae en `ALTO MAGDALENA`, la zona con más datos (~49 M de filas). |
| `latitud` | number | Latitud de la estación (grados decimales) | 791 valores distintos. Precisión variable (`4.567` o `3.908388889`). |
| `longitud` | number | Longitud de la estación (grados decimales) | 793 valores distintos. **El valor máximo es `0`**: hay estaciones con coordenadas inválidas que hay que descartar. |
| `descripcionsensor` | text | Descripción del sensor | Constante: `Precipitacion`. |
| `unidadmedida` | text | Unidad de medida | Constante: `mm`. |

Tamaño total según el portal: **~165,3 millones de filas**.

#### Implicaciones para las consultas

- `codigosensor`, `descripcionsensor` y `unidadmedida` no aportan nada al filtrar: se
  pueden omitir del `$select`.
- Filtrar el Huila con `departamento = 'HUILA'` (sin tilde). Para otros departamentos
  hay que respetar las tildes o normalizar el texto.
- Con ~9 M de filas solo para el Huila, conviene **agregar en el servidor** (totales
  diarios con `date_trunc_ymd` y `sum`) en vez de bajar las lecturas de 10 minutos.
- Un día completo tiene 144 lecturas; sirve para medir qué tan completo está cada día.
- Las coordenadas vienen en cada fila (no hay una tabla aparte de estaciones), así que
  el catálogo de estaciones se arma agrupando por `codigoestacion`.

### Por verificar

Cosas que los metadatos sugieren pero que hay que confirmar con una consulta real antes
de confiar en ellas:

- **Rango de fechas.** La caché dice que los datos van de 2003-01-20 a 2022-04-26, pero
  el portal reporta filas actualizadas el 2026-10-25. O la caché está vieja, o los datos
  recientes llegan con otro patrón. Consultar `min` y `max` de `fechaobservacion` para
  el Huila.
- **Zona horaria** de `fechaobservacion`: se asume hora local de Colombia (UTC−5), pero
  el campo no la declara. Importa al sumar días para compararlos con NASA POWER e IMERG.
- **Conteos inconsistentes en la caché**: el portal reporta 165,3 M de valores no nulos
  y, en el mismo bloque, 116,3 M en otro campo. Tomar los conteos como orden de magnitud.
- **Valor `6.7` sospechoso**: es el 11.º valor más frecuente (~114 000 lecturas), más
  común que 0.9 o 1.2 mm. Puede ser un valor de relleno o una falla de algún sensor;
  revisar en qué estaciones aparece.
- **Resolución del pluviómetro**: casi todo viene en pasos de 0.1 mm, pero hay ~56 000
  lecturas de `0.01`, lo que sugiere sensores con otra resolución.
- **Estaciones con `longitud = 0`**: identificar cuáles son y si alguna está en el Huila.


### Avisos de calidad y condiciones de uso

El IDEAM publica estos datos con las siguientes condiciones (resumidas):

1. **No están validados por el IDEAM.** Son datos crudos e instantáneos de los sensores
   de la red propia o de convenios con otras entidades.
2. **Pueden tener retraso**, según la frecuencia de envío de cada sensor y el medio de
   transmisión.
3. **Pueden tener errores o inconsistencias**, incluso valores fuera de lo normal por
   fallas de los sensores. Para usos técnicos se recomienda aplicar verificaciones
   adicionales.
4. **El uso e interpretación son responsabilidad de quien usa los datos.** El IDEAM no
   está obligado a justificarlos ni a validarlos después; la información oficial y
   validada se obtiene por sus canales oficiales.
5. **No sirven como evidencia jurídica** ante entes de control sobre la ocurrencia o no
   de fenómenos hidroclimatológicos.
6. Se publican como mecanismo de transparencia y apoyo a la gestión del riesgo, en
   cumplimiento de la Ley 1712 de 2014 (transparencia y acceso a la información pública).

**Qué implica para nosotros:** antes de comparar con NASA hay que aplicar nuestro propio
control de calidad (descartar días con pocas observaciones y totales imposibles) y, en
la presentación, hablar de "estaciones del IDEAM" como referencia en tierra, no como
verdad absoluta.

### Atribución

Al usar o mostrar estos datos (por ejemplo, en la demo o en las diapositivas):

> Datos de precipitación: IDEAM, publicados en datos.gov.co (dataset `s54a-sgyg`), licencia CC BY-SA 4.0.

Si publicamos un derivado de estos datos (por ejemplo, una tabla de totales diarios por
estación), la licencia CC BY-SA exige compartirlo con la misma licencia.

---