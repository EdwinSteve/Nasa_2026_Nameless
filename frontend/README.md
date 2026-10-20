# Frontend SURCO (Next.js)

Interfaz web de SURCO: registro del productor, mapa del lote, planificador de rotación y simulador. Fase 3 del [roadmap](../docs/02-roadmap.md). El diseño se trabaja en Stitch y se traduce a componentes aquí.

## Cómo correrlo

Primero el backend en `http://localhost:8000` (ver [backend/README.md](../backend/README.md)). Luego:

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000 → redirige a /registro
```

Next.js reenvía `/api/v1/*` al backend (`next.config.ts`), así que en desarrollo no hace falta CORS. Variables opcionales en `.env.local`:

| Variable | Para qué | Por defecto |
|---|---|---|
| `BACKEND_URL` | A dónde reenvía Next.js las llamadas `/api/v1` | `http://localhost:8000` |
| `NEXT_PUBLIC_API_URL` | Si se define, el navegador llama a esa URL directamente (necesita `CORS_ORIGENES` en el backend) | vacía |

Otros comandos: `npm run build` (compila y revisa tipos), `npm run lint`.

## Estructura

```
src/
  app/                     rutas de Next.js (solo envoltorios delgados)
    registro/page.tsx      /registro → RegistroWizard
    lotes/[loteId]/        /lotes/:id → diagnóstico (provisional)
    politica-de-datos/     texto de la política vigente
  routes/                  pantallas completas, independientes del router
    RegistroWizard.tsx     wizard de 4 pasos: datos, finca, lote, prioridades
  components/
    forms/                 SelectField, PhoneInput, ConsentCard, CropChipSelector,
                           MapDrawer, PriorityRanker, StepperProgress
    feedback/              ErrorCard
  api/
    tipos.ts               contratos con FastAPI /api/v1
    services.ts            una función por endpoint
    http.ts                cliente: errores al formato ErrorApi y renovación del token
    sesion.ts              tokens de la sesión
  lib/
    geo.ts                 utilidades geográficas (área del polígono en ha)
```

Las pantallas en `src/routes/` reciben `onNavigate` en lugar de usar el router directamente, así se pueden probar solas.

## Estado de la integración

- **Conectado al backend:** política, registro, municipios y corregimientos (DIVIPOLA), finca, lote, preferencias y diagnóstico satelital con datos reales de la NASA.
- **Registro:** el módulo identidad usa nombres en inglés (`full_name`, `phone`...). `services.ts` los traduce y los errores de campo vuelven con los nombres del formulario.
- **Sesión:** los tokens se guardan en `localStorage` y el access token se renueva solo con el refresh token. Pendiente de seguridad: pasar el refresh token a una cookie httpOnly.
- **Área del lote:** la UI muestra una estimación mientras se dibuja; el área oficial la calcula el backend.
- **Pendiente:** `MapDrawer` sigue siendo un marcador de posición. "Caminar el borde" (demo) y "Coordenadas" ya generan un polígono, pero "Tocar esquinas" se conectará a Leaflet. Tampoco existen aún `/ingresar` ni la ficha del lote.

## Convenciones de UI

- Zonas táctiles de al menos 56×56 px.
- Cada input tiene `<label htmlFor>`; los errores usan `aria-live="polite"`.
- Grupos de opciones en `<fieldset>` + `<legend>`, con botones `aria-pressed`.
- TypeScript estricto: sin `as any` ni aserciones `!`.
- Paleta: verde `#1F4D2B`, crema `#F7F3EA`, tinta `#14202B`, error `#D94F4F`.
