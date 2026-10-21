// src/lib/plan.ts
// Textos y reglas del plan de siembra. Sin React: se prueban solas.
import type { CultivoRanking, ErrorApi, LluviaMensual, Plan, Rotacion } from '../api/tipos';
import { formatearDiaMes } from './fechas';

const decimales = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const diaMesUtc = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'numeric', timeZone: 'UTC' });

/** Los cultivos aptos primero, del que más le conviene al que menos; los no aptos al final. */
export function ordenarRanking(ranking: CultivoRanking[]): CultivoRanking[] {
  return [...ranking].sort((a, b) => Number(b.apto) - Number(a.apto) || b.ip - a.ip);
}

/** 0.83 → "0,83" */
export function formatearIp(ip: number): string {
  return decimales.format(Math.max(0, Math.min(1, ip)));
}

/** 8 → "8 de cada 10 años le va bien" */
export function textoFrecuencia(frecuencia: number): string {
  return `${frecuencia} de cada 10 años le va bien`;
}

/** "Mejor época: del 8 al 22 de marzo" o, si cambia de mes, "del 25 de febrero al 10 de marzo". */
export function textoMejorEpoca(inicio: string, fin: string): string {
  const mismoMes = inicio.slice(0, 7) === fin.slice(0, 7);
  if (inicio === fin) return `Mejor época: el ${formatearDiaMes(inicio)}`;
  if (mismoMes) {
    const dia = Number(inicio.slice(8, 10));
    return `Mejor época: del ${dia} al ${formatearDiaMes(fin)}`;
  }
  return `Mejor época: del ${formatearDiaMes(inicio)} al ${formatearDiaMes(fin)}`;
}

/** "Si siembra el 15 de abril: 5 de cada 10 años" */
export function textoSiSiembra(fecha: string, frecuencia: number): string {
  return `Si siembra el ${formatearDiaMes(fecha)}: ${frecuencia} de cada 10 años`;
}

/** Fecha corta para el eje de la gráfica: "8/3". */
export function fechaEje(fecha: string): string {
  return diaMesUtc.format(new Date(`${fecha.slice(0, 10)}T00:00:00Z`));
}

// --- Controles de "¿Y si el clima cambia?" ---

export const LLUVIA = { min: -40, max: 20, paso: 10 } as const;
export const TEMPERATURA = { min: 0, max: 4, paso: 1 } as const;

/** -20 → "20 % menos lluvia"; 0 → "La lluvia de siempre"; 10 → "10 % más lluvia". */
export function textoLluvia(delta: number): string {
  if (delta === 0) return 'La lluvia de siempre';
  return `${Math.abs(delta)} % ${delta < 0 ? 'menos' : 'más'} lluvia`;
}

/** 0 → "El calor de siempre"; 1 → "1 grado más de calor"; 3 → "3 grados más de calor". */
export function textoTemperatura(delta: number): string {
  if (delta === 0) return 'El calor de siempre';
  return `${delta} ${delta === 1 ? 'grado' : 'grados'} más de calor`;
}

// --- Calendario de lluvias ---

export interface LluviaEnPalabras {
  texto: string;
  /** Cuántas gotas dibujar; 0 = se dibuja un sol. */
  gotas: 0 | 1 | 2 | 3;
}

export function lluviaEnPalabras(mes: Pick<LluviaMensual, 'nivel' | 'lluvia_mm'>): LluviaEnPalabras {
  if (mes.nivel === 'seco') return { texto: 'Poca lluvia', gotas: 0 };
  if (mes.nivel === 'normal') return { texto: 'Lluvia normal', gotas: mes.lluvia_mm >= 100 ? 2 : 1 };
  return { texto: mes.lluvia_mm >= 180 ? 'Muchas lluvias' : 'Buenas lluvias', gotas: 3 };
}

// --- Navegación entre el plan y el detalle ---

/**
 * La rotación que se acepta desde el detalle de un cultivo: la pedida si existe y lo incluye;
 * si no, la mejor que lo incluya. null si ninguna rotación tiene ese cultivo.
 */
export function rotacionParaCultivo(plan: Plan, cultivo_id: string, rotacion_id: string | null): Rotacion | null {
  const incluye = (r: Rotacion) => r.secuencia.some((c) => c.cultivo_id === cultivo_id);
  const pedida = plan.rotaciones.find((r) => r.id === rotacion_id);
  if (pedida && incluye(pedida)) return pedida;
  return plan.rotaciones.find(incluye) ?? null;
}

/** El nombre de un cultivo dentro del plan (ranking o rotaciones). */
export function nombreCultivo(plan: Plan, cultivo_id: string): string | null {
  const enRanking = plan.ranking.find((c) => c.cultivo_id === cultivo_id);
  if (enRanking) return enRanking.nombre;
  for (const r of plan.rotaciones) {
    const c = r.secuencia.find((s) => s.cultivo_id === cultivo_id);
    if (c) return c.nombre;
  }
  return null;
}

/** El tarea_id que manda el backend en un 409 PLAN_EN_CALCULO. */
export function tareaEnCurso(error: ErrorApi): string | null {
  if (error.codigo !== 'PLAN_EN_CALCULO') return null;
  return error.detalles?.find((d) => d.campo === 'tarea_id')?.mensaje ?? null;
}
