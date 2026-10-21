# Frontend SURCO (Next.js)

Interfaz web de SURCO: registro del productor, mapa del lote, planificador de rotación y simulador. Fase 3 del [roadmap](../docs/02-roadmap.md). El diseño se trabaja en Stitch y se traduce a componentes aquí.

## Cómo correrlo

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000 → redirige a /registro
```

Otros comandos: `npm run build` (compila y revisa tipos), `npm run lint`.

## Estructura

```
src/
  app/                     rutas de Next.js (solo envoltorios delgados)
    registro/page.tsx      /registro → RegistroWizard
    lotes/[loteId]/        /lotes/:id → diagnóstico (provisional)
  routes/                  pantallas completas, independientes del router
    RegistroWizard.tsx     wizard de 4 pasos: datos, finca, lote, prioridades
  components/
    forms/                 SelectField, PhoneInput, ConsentCard, CropChipSelector,
                           MapDrawer, PriorityRanker, StepperProgress
    feedback/              ErrorCard
  api/
    tipos.ts               contratos con FastAPI /api/v1
    services.ts            una función por endpoint (hoy son stubs con datos de ejemplo)
  lib/
    geo.ts                 utilidades geográficas (área del polígono en ha)
```

Las pantallas en `src/routes/` reciben `onNavigate` en lugar de usar el router directamente, así se pueden probar solas.

## Estado de la integración

- `src/api/services.ts` devuelve datos falsos y escribe en consola el endpoint que llamaría. Para conectar el backend, se reemplaza el cuerpo de cada función por el `fetch` real; los componentes no cambian.
- `MapDrawer` es un marcador de posición: los modos "Caminar el borde" (demo) y "Coordenadas" ya generan un polígono, pero "Tocar esquinas" se conectará a Leaflet.

## Convenciones de UI

- Zonas táctiles de al menos 56×56 px.
- Cada input tiene `<label htmlFor>`; los errores usan `aria-live="polite"`.
- Grupos de opciones en `<fieldset>` + `<legend>`, con botones `aria-pressed`.
- TypeScript estricto: sin `as any` ni aserciones `!`.
- Paleta: verde `#1F4D2B`, crema `#F7F3EA`, tinta `#14202B`, error `#D94F4F`.
