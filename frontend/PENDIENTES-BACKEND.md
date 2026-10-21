# Pendientes del backend para la pantalla Inicio

La pantalla `/inicio` usa dos endpoints que el backend todavía no tiene. Mientras tanto el frontend los simula con datos de demostración (ver [Cómo probar sin backend](#cómo-probar-sin-backend)).

Ambos van bajo `/api/v1`, piden `Authorization: Bearer <access_token>` y responden los errores con el formato de siempre: `{ "code": "...", "message": "...", "details": {...} }`. Los tipos de TypeScript están en [src/api/tipos.ts](src/api/tipos.ts) (`ResumenInicio`, `RiegoRegistrado`).

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
    "mensaje": "Riega tu maíz esta semana: unos 450 m³ por hectárea. ...",
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

## Cómo probar sin backend

En `frontend/.env.local`:

```bash
NEXT_PUBLIC_USAR_MOCKS=inicio          # o inicio:nuevo, inicio:sin-lote
```

Con eso, solo `GET /inicio` y `POST /lotes/{id}/riegos` usan los datos de [src/api/mocks/inicio.ts](src/api/mocks/inicio.ts); el resto sigue yendo al backend. El escenario también se cambia desde la URL:

- `/inicio?demo=historia` — productor con cultivo, recomendación de riego, logros y gráficas.
- `/inicio?demo=nuevo` — usuario nuevo: lote sin cultivo, sin logros ni gráficas.
- `/inicio?demo=sin-lote` — todavía no ha marcado ningún lote.

Después de cambiar `.env.local` hay que reiniciar `npm run dev`. Cuando el backend tenga los dos endpoints, basta con quitar `inicio` de la variable.
