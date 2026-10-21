// src/lib/planGuardado.ts
// Último plan y lluvias de cada lote guardados en el navegador, para mostrarlos sin conexión.
import type { LluviaMensual, Plan } from '../api/tipos';

export interface PlanGuardado {
  plan: Plan;
  lluvias: LluviaMensual[] | null;
}

const clave = (lote_id: string) => `surco.plan.${lote_id}`;

export function guardarPlan(lote_id: string, datos: PlanGuardado): void {
  try {
    localStorage.setItem(clave(lote_id), JSON.stringify(datos));
  } catch {
    // Sin espacio o almacenamiento bloqueado: la pantalla funciona igual, solo sin copia
  }
}

export function leerPlanGuardado(lote_id: string): PlanGuardado | null {
  try {
    const texto = localStorage.getItem(clave(lote_id));
    if (!texto) return null;
    const datos = JSON.parse(texto) as PlanGuardado;
    return datos.plan?.lote_id === lote_id ? datos : null;
  } catch {
    return null;
  }
}

/** El plan guardado que tenga este id, en cualquier lote (para el detalle sin conexión). */
export function buscarPlanGuardado(plan_id: string): Plan | null {
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (!k?.startsWith('surco.plan.')) continue;
      const datos = JSON.parse(localStorage.getItem(k) ?? 'null') as PlanGuardado | null;
      if (datos?.plan.id === plan_id) return datos.plan;
    }
  } catch {
    // Igual que arriba
  }
  return null;
}
