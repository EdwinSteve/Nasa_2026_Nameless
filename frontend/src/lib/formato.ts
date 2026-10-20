// src/lib/formato.ts
const hectareas = new Intl.NumberFormat('es-CO', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1
});

/** 6.4 → "6,4" (formato colombiano, sin la unidad) */
export function formatearHectareas(valor: number): string {
  return hectareas.format(valor);
}
