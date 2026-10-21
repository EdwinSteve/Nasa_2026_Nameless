# Pendientes del backend

Las pantallas Inicio (`/inicio`), Plan de siembra (`/plan`) y Asistente (`/asistente`) usan endpoints que el backend todavía no tiene. Mientras tanto el frontend los simula con datos de demostración (ver [Cómo probar sin backend](#cómo-probar-sin-backend)).

Todos van bajo `/api/v1`, piden `Authorization: Bearer <access_token>` y responden los errores con el formato de siempre: `{ "code": "...", "message": "...", "details": {...} }`. Los tipos de TypeScript están en [src/api/tipos.ts](src/api/tipos.ts).

Los textos que manda el backend (`mensaje`, `nota`, `razones`, `razon_no_apto`, `mensaje_estado`, las respuestas del asistente) van de **usted**, en palabras sencillas y sin nombres técnicos: esos solo van en `procedencia.fuente`.

# Pantalla Inicio

## GET /inicio

Todo lo que necesita la pantalla de inicio del usuario autenticado, en una sola llamada.

**Respuesta 200**

```jsonc
{
  "usuario": { "nombre": "Ernesto" },              // solo el primer nombre, para el saludo
  "clima_hoy": {
    "temperatura_c": 31,
    "estado": "soleado",                           // "soleado" | "nublado" | "lluvia"
    "probabilidad_lluvia_pct": 10,
    "procedencia": { "fuente": "NASA POWER", "fecha": "2026-10-20" }
  },
  "recomendacion_hoy": {                           // null = hoy no hay nada especial que hacer
    "tipo": "riego",                               // "riego" | "siembra" | "cosecha" | "alerta" | "ninguna"
    "mensaje": "Riegue su maíz esta semana: unos 450 m³ por hectárea. ...",
    "detalle_porque": "La humedad en la zona de las raíces está en 12 % ...",
    "procedencia": { "fuente": "NASA SMAP", "fecha": "2026-10-18" }
  },
  "lote_principal": {                              // null = todavía no ha marcado ningún lote
    "id": "uuid-del-lote",
    "nombre": "La Vega",
    "area_ha": 6.4,
    "corregimiento_nombre": "Fortalecillas",
    "altitud_msnm": 442,                           // puede ser null
    "poligono": { "type": "Polygon", "coordinates": [[[-75.29, 2.99], "..."]] },
    "cultivo": {                                   // null = el lote no tiene cultivo sembrado
      "nombre": "Maíz",
      "dia_actual": 54,
      "dias_ciclo": 120,
      "etapa_actual": "floracion",                 // "siembra" | "crecimiento" | "floracion" | "llenado" | "cosecha"
      "fecha_cosecha_estimada": "2026-12-25"
    },
    "indicadores": {
      "humedad": { "nivel": "malo",  "etiqueta": "Baja",   "procedencia": { "fuente": "NASA SMAP",  "fecha": "2026-10-18" } },
      "verdor":  { "nivel": "bueno", "etiqueta": "Bueno",  "procedencia": { "fuente": "NASA HLS",   "fecha": "2026-10-15" } },
      "calor":   { "nivel": "bueno", "etiqueta": "Normal", "procedencia": { "fuente": "NASA POWER", "fecha": "2026-10-20" } }
    }
  },
  "alertas_pendientes": 2,
  "logros": {                                      // null = usuario nuevo, sin historia todavía
    "agua_ahorrada_m3": 1840,
    "nitrogeno_kg": 48,
    "salud_suelo": 72,                             // 0 a 100
    "salud_suelo_cambio": 9,                       // puntos frente al inicio; negativo si bajó
    "frecuencia_exito": 8                          // "8 de cada 10 años"
  },
  "series": {                                      // null = usuario nuevo
    "agua_mensual": [{ "mes": "2026-05", "usada_m3_ha": 510, "recomendada_m3_ha": 450 }],
    "salud_suelo":  [{ "mes": "2025-11", "valor": 63 }]
  }
}
```

Reglas que asume el frontend:

- Fechas como `AAAA-MM-DD` y meses como `AAAA-MM`. Las series vienen en orden cronológico; el frontend no las reordena.
- `EstadoSimple.nivel` puede ser `"sin_dato"` con `procedencia: null` cuando aún no hay dato (por ejemplo, verdor de un lote recién marcado).
- `mensaje` y `detalle_porque` van en palabras sencillas, sin nombres técnicos. Los nombres de las fuentes (NASA SMAP, HLS, POWER) solo van en `procedencia.fuente`.
- Si `mensaje` trae una cantidad en m³ (`450 m³`), el frontend la resalta.
- Si `recomendacion_hoy.tipo` es `"riego"`, la tarjeta muestra el botón "Ya regué", que llama a `POST /lotes/{id}/riegos` con el `lote_principal.id`.

**Errores:** `401` sin sesión o token vencido (el cliente intenta refrescar el token y, si no puede, manda al ingreso).

## POST /lotes/{lote_id}/riegos

Registra que el productor ya regó el lote (botón "Ya regué").

**Cuerpo:** `{}` por ahora. Si más adelante se pide la cantidad, iría como `{ "cantidad_m3": 450 }` opcional.

**Respuesta 201**

```json
{ "riego_id": "uuid", "lote_id": "uuid-del-lote", "registrado_en": "2026-10-20T14:32:00Z" }
```

**Errores:** `401` sin sesión, `403` si el lote no es del usuario, `404` si el lote no existe.

Sugerencia: después de registrar el riego, `GET /inicio` debería dejar de recomendar riego para ese lote ese día, y el riego debería sumar a `logros.agua_ahorrada_m3` y a `series.agua_mensual`.

# Plan de siembra

Pantallas `/plan` (plan del lote) y `/plan/{plan_id}/cultivo/{cultivo_id}` (detalle de un cultivo). Los `cultivo_id` son los del catálogo (`maiz`, `arroz_riego`, `soya`…). La frecuencia siempre va como entero de 0 a 10 ("8 de cada 10 años"), nunca como porcentaje.

## GET /lotes

Los lotes del usuario autenticado, para el selector de lote. **200:** `[{ "id": "uuid", "nombre": "La Vega", "area_ha": 6.4 }]` (lista vacía si no tiene lotes).

## POST /lotes/{lote_id}/planes

Empieza a armar el plan de siembra del lote en segundo plano. **Cuerpo:** `{}`. **202:** `{ "tarea_id": "uuid" }`.

**Errores:** `404 LOTE_NO_ENCONTRADO`, `409 DIAGNOSTICO_NO_DISPONIBLE` si el lote todavía no tiene diagnóstico satelital (la pantalla muestra "Primero necesitamos analizar su lote").

## GET /lotes/{lote_id}/planes/tareas/{tarea_id}

Avance de la tarea; la pantalla la consulta cada 1,5 s y la muestra con el mismo componente del diagnóstico. **No estaba en el pedido original:** hace falta porque `POST /planes` solo devuelve el `tarea_id`. Misma forma que `GET /lotes/{id}/diagnostico/{tarea_id}`, más `plan_id`:

```jsonc
{
  "tarea_id": "uuid", "lote_id": "uuid", "nombre_lote": "La Vega", "area_ha": 6.4,
  "corregimiento_nombre": "Fortalecillas", "municipio_nombre": "Neiva", "poligono": null,
  "estado": "en_proceso",                  // "pendiente" | "en_proceso" | "lista" | "fallida"
  "progreso": 34,
  "paso_activo_codigo": "pronostico",      // "historia" | "pronostico" | "suelo" | "rotaciones"
  "mensaje_estado": "Revisando: Pronóstico de El Niño y La Niña…",
  "pasos": [
    { "codigo": "historia", "nombre": "40 años de clima de su zona", "estado": "lista", "progreso": 100,
      "fuente": "NASA POWER", "resumen": "Dos temporadas de lluvia al año." }
  ],
  "plan_id": null                          // trae el id cuando estado = "lista"
}
```

## GET /lotes/{lote_id}/plan

El último plan del lote. **200:** un `Plan` (ver abajo).

**Errores** (la pantalla elige qué mostrar según el código):

| Código | HTTP | Qué muestra |
|---|---|---|
| `PLAN_NO_DISPONIBLE` | 404 | "Armar mi plan de siembra" |
| `DIAGNOSTICO_NO_DISPONIBLE` | 409 | "Primero necesitamos analizar su lote" |
| `PLAN_EN_CALCULO` | 409 | El progreso de la tarea. Debe traer `details: [{ "field": "tarea_id", "message": "<uuid>" }]` |

## GET /planes/{plan_id}

```jsonc
{
  "id": "uuid", "lote_id": "uuid", "calculado_en": "2026-10-19T14:00:00Z",
  "rotaciones": [                          // las mejores primero; la pantalla muestra hasta 3
    {
      "id": "uuid", "grado": "A",          // "A" | "B" | "C" | "D"
      "secuencia": [{ "cultivo_id": "maiz", "nombre": "Maíz" }, { "cultivo_id": "soya", "nombre": "Soya" }, { "cultivo_id": "sorgo", "nombre": "Sorgo" }],
      "frecuencia_exito": 8,
      "agua_ahorrada_m3": 2100,
      "aporte_nitrogeno": "La soya le deja al sorgo unos 60 kg de nitrógeno por hectárea",   // o null
      "razones": [{ "texto": "…", "procedencia": { "fuente": "NASA POWER", "fecha": "2026-10-20" } }]
    }
  ],
  "ranking": [                             // en cualquier orden: el frontend pone los no aptos al final
    { "cultivo_id": "arroz_riego", "nombre": "Arroz", "ip": 0.83, "apto": true, "razon_no_apto": null },
    { "cultivo_id": "cafe", "nombre": "Café", "ip": 0.12, "apto": false, "razon_no_apto": "Su zona es muy caliente para el café." }
  ]
}
```

`ip` va de 0 a 1. Cuando `apto` es `false`, `razon_no_apto` debería venir siempre.

## GET /lotes/{lote_id}/lluvias-esperadas

Lluvia esperada mes a mes desde el mes actual (la pantalla muestra lo que llegue; el mock trae 6 meses).

```json
[{ "mes": "2026-10", "lluvia_mm": 170, "nivel": "lluvioso", "nota": "Buenas lluvias para que germine la semilla.",
   "procedencia": { "fuente": "NASA POWER", "fecha": "2026-10-20" } }]
```

`nivel`: `"seco" | "normal" | "lluvioso"` (con sol, una o dos gotas, o tres gotas). `nota` puede ser `null`.

## GET /planes/{plan_id}/ventana-siembra?cultivo={cultivo_id}

Frecuencia de éxito según la fecha de siembra en los próximos 6 meses (el mock trae un punto por semana).

```json
{
  "cultivo_id": "maiz",
  "puntos": [{ "fecha": "2026-10-20", "frecuencia_exito": 4 }],
  "mejor_inicio": "2027-03-02",
  "mejor_fin": "2027-03-16",
  "razones": [{ "texto": "En esas semanas llegan las lluvias justo cuando la planta más agua necesita.",
                "procedencia": { "fuente": "NASA POWER", "fecha": "2026-10-20" } }]
}
```

Los puntos van en orden de fecha; `mejor_inicio` y `mejor_fin` deberían coincidir con fechas de `puntos`.

## POST /planes/{plan_id}/escenarios

¿Cuántos años de cada 10 le iría bien si cambia el clima? La pantalla lo llama 400 ms después de que el productor deja de mover los controles.

**Cuerpo:** `{ "cultivo_id": "maiz", "delta_lluvia_pct": -20, "delta_temp_c": 2 }` (lluvia de −40 a +20 en pasos de 10; temperatura de 0 a +4 en pasos de 1). **200:** `{ "frecuencia_exito": 6 }`.

Con `0` y `0` la pantalla no llama: usa la frecuencia de la mejor época de la ventana de siembra.

## POST /planes/{plan_id}/aceptar

El productor elige una rotación ("Elegir este plan"). **Cuerpo:** `{ "rotacion_id": "uuid" }`. **200:** `{ "plan_id": "uuid", "rotacion_id": "uuid", "aceptado_en": "2026-10-20T15:00:00Z" }`.

**Errores:** `404` si el plan o la rotación no existen, `403` si el plan no es de un lote del usuario.

# Asistente SURCO

Pantalla `/asistente?lote=&cultivo=&plan=` (`cultivo` y `plan` llegan desde el detalle de un cultivo del Plan). Es un chat con una inteligencia artificial que responde con los datos del lote.

**Reglas para las respuestas** (las hace cumplir el backend, no la pantalla):

- Se presenta como "Asistente SURCO", una inteligencia artificial. Nunca con nombre ni cargo de persona.
- Responde de usted, corto y con los mismos datos que muestran Inicio y el Plan, sin contradecirlos. Ejemplo: si Inicio dice humedad "Baja", el asistente no dice "la tierra está bien".
- No recomienda abonos, fertilizantes ni agroquímicos, no habla de plagas ni da precios. En esos casos dice que no tiene datos confiables y remite al técnico agrícola.
- Cada dato puntual va en una `TarjetaDato`, con su fuente en `procedencia`.

## GET /asistente/conversaciones?lote_id={lote_id}

**200:**

```jsonc
{
  "usuario": { "nombre": "Ernesto" },      // para el saludo "Hola, Ernesto"
  "lote_id": "uuid",
  "mensajes": [                            // del más viejo al más nuevo; [] la primera vez
    {
      "id": "uuid", "rol": "productor", "creado_en": "2026-10-20T12:14:00Z",
      "texto": "¿Será que riego el maíz esta semana?",   // en una nota de voz, la transcripción
      "audio_duracion_s": 4,               // null si fue texto
      "tarjetas": [], "enlaces": []
    },
    {
      "id": "uuid", "rol": "asistente", "creado_en": "2026-10-20T12:14:03Z",
      "texto": "Sí, Ernesto. La tierra de su lote La Vega está seca para un maíz en floración. Riegue esta semana unos 450 m³ por hectárea.",
      "audio_duracion_s": null,
      "tarjetas": [
        { "etiqueta": "Humedad de la tierra", "valor": "Baja", "unidad": null,
          "procedencia": { "fuente": "NASA SMAP", "fecha": "2026-10-18" } },
        { "etiqueta": "Lluvia de los últimos 7 días", "valor": "3", "unidad": "mm",
          "procedencia": { "fuente": "NASA POWER", "fecha": "2026-10-20" } }
      ],
      "enlaces": [{ "texto": "Ver en mi lote", "ruta": "/lotes/uuid" }]
    }
  ]
}
```

`usuario` no estaba en el pedido original: va aquí porque el backend no tiene `GET /usuarios/me` y el saludo necesita el nombre. `valor` va como texto ya listo para mostrar ("Baja", "3", "8 de cada 10"). `enlaces[].ruta` es una ruta de la app (`/lotes/{id}`, `/plan?lote={id}`).

**Errores:** `404 LOTE_NO_ENCONTRADO`.

## POST /asistente/mensajes

La pregunta del productor. **Cuerpo:**

```json
{ "lote_id": "uuid", "texto": "¿Debo regar hoy?", "audio_duracion_s": null }
```

`audio_duracion_s` (opcional, no estaba en el pedido original) va con la duración en segundos cuando la pregunta fue una nota de voz; `texto` es entonces la transcripción. El backend guarda los dos mensajes (el del productor y el suyo).

**200:** el `MensajeAsistente` con la respuesta (`rol: "asistente"`). La pantalla pinta el mensaje del productor apenas se envía; si la petición falla, ese mensaje queda con "No se envió · Reintentar" y se reenvía igual.

## POST /asistente/transcripciones

La nota de voz en texto. **Cuerpo:** `multipart/form-data` con el campo `audio`: `audio/webm` (Chrome, Android) o `audio/mp4` (Safari, iPhone), de 60 s como máximo. **200:** `{ "texto": "¿Será que riego el maíz esta semana?" }`.

**Errores:** `413` si pasa del tamaño máximo, `422` si no se entendió nada (la pantalla deja la nota con "No se envió · Reintentar").

## POST /asistente/mensajes/{mensaje_id}/valoracion

"Me sirvió" / "No me sirvió" sobre una respuesta. **Cuerpo:** `{ "util": true }`. **204** sin cuerpo. Se puede cambiar: la última valoración reemplaza la anterior.

## GET /lotes/{lote_id}/resumen

Panel derecho del asistente en escritorio. **No estaba en el pedido original.** **200:** el mismo objeto que `lote_principal` de `GET /inicio` (nombre, área, corregimiento, altitud, polígono, cultivo con su etapa e indicadores), pero para cualquier lote del usuario.

# Cómo probar sin backend

En `frontend/.env.local`:

```bash
NEXT_PUBLIC_USAR_MOCKS=inicio,plan,asistente     # o inicio:nuevo, plan:sin-plan...
```

Cada grupo simula solo sus endpoints; el resto sigue yendo al backend. `inicio` usa [src/api/mocks/inicio.ts](src/api/mocks/inicio.ts), `plan` usa [src/api/mocks/plan.ts](src/api/mocks/plan.ts) y `asistente` usa [src/api/mocks/asistente.ts](src/api/mocks/asistente.ts) (`GET /lotes` se simula con `plan` o con `asistente`). El escenario también se cambia desde la URL con `?demo=`.

Inicio:

- `/inicio?demo=historia` — productor con cultivo, recomendación de riego, logros y gráficas.
- `/inicio?demo=nuevo` — usuario nuevo: lote sin cultivo, sin logros ni gráficas.
- `/inicio?demo=sin-lote` — todavía no ha marcado ningún lote.

Plan de siembra:

- `/plan?demo=con-plan`: tres rotaciones, el ranking (con el café como no apto) y las lluvias.
- `/plan?demo=sin-plan`: botón "Armar mi plan de siembra", que muestra el progreso (unos 6 s) y luego el plan.
- `/plan?demo=sin-diagnostico`: "Primero necesitamos analizar su lote". El botón llama al diagnóstico real, así que sin backend muestra un error.
- `/plan?demo=calculando`: el plan ya se está armando y se ve el progreso.
- `/plan?demo=error`: falla la primera vez; "Intentar de nuevo" lo carga.

Asistente:

- `/asistente?demo=con-historia`: la nota de voz sobre riego y su respuesta con dos tarjetas.
- `/asistente?demo=nuevo`: primera vez, con el saludo y las preguntas sugeridas.
- `/asistente?demo=falla-envio`: el primer mensaje falla ("No se envió · Reintentar") y al reintentar llega.
- Cualquier nota de voz se transcribe como "¿Será que riego el maíz esta semana?". Las respuestas cambian según el tema: riego, siembra, suelo, lluvia, "¿Por qué me recomiendan…?", y abonos, plagas o precios (remite al técnico).

Después de cambiar `.env.local` hay que reiniciar `npm run dev`. Cuando el backend tenga los endpoints de un grupo, basta con quitar ese grupo de la variable.
