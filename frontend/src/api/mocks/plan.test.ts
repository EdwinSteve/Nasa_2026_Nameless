import { describe, expect, it } from 'vitest';
import { DURACION_TAREA_MS, escenarioDemo, LOTES_DEMO, lluviasDemo, planDemo, tareaPlanDemo, ventanaDemo } from './plan';

const HOY = new Date(2026, 9, 20, 9);

describe('mock del plan de siembra', () => {
  it('trae las rotaciones y el ranking acordados para el valle de Neiva', () => {
    const plan = planDemo('lote-1', HOY);
    expect(plan.rotaciones.map((r) => [r.grado, r.frecuencia_exito])).toEqual([
      ['A', 8],
      ['B', 7],
      ['B', 7]
    ]);
    expect(plan.rotaciones[0].agua_ahorrada_m3).toBe(2100);
    expect(plan.ranking.find((c) => c.cultivo_id === 'cafe')?.apto).toBe(false);
  });

  it('las lluvias empiezan en el mes actual', () => {
    const meses = lluviasDemo(HOY);
    expect(meses.map((m) => m.mes)).toEqual(['2026-10', '2026-11', '2026-12', '2027-01', '2027-02', '2027-03']);
    expect(meses[0].nivel).toBe('lluvioso');
  });

  it('la ventana de siembra cubre 6 meses desde hoy y la mejor época tiene la frecuencia más alta', () => {
    const v = ventanaDemo('maiz', HOY);
    expect(v.puntos[0].fecha).toBe('2026-10-20');
    expect(v.puntos).toHaveLength(26);
    const maximo = Math.max(...v.puntos.map((p) => p.frecuencia_exito));
    const dentro = v.puntos.filter((p) => p.fecha >= v.mejor_inicio && p.fecha <= v.mejor_fin);
    expect(dentro.length).toBeGreaterThan(0);
    expect(dentro.every((p) => p.frecuencia_exito === maximo)).toBe(true);
    expect(v.mejor_inicio.slice(0, 7)).toBe('2027-03');
  });

  it('menos lluvia o más calor bajan la frecuencia, sin salirse de 0 a 10', () => {
    expect(escenarioDemo(8, 0, 0)).toBe(8);
    expect(escenarioDemo(8, -20, 0)).toBeLessThan(8);
    expect(escenarioDemo(8, 0, 3)).toBeLessThan(8);
    expect(escenarioDemo(8, -40, 4)).toBeGreaterThanOrEqual(0);
    expect(escenarioDemo(10, 20, 0)).toBeLessThanOrEqual(10);
  });

  it('la tarea avanza paso a paso y al terminar trae el plan', () => {
    const lote = LOTES_DEMO[0];
    const empezando = tareaPlanDemo(lote, 0);
    expect(empezando.estado).toBe('en_proceso');
    expect(empezando.plan_id).toBeNull();
    const mitad = tareaPlanDemo(lote, DURACION_TAREA_MS / 2);
    expect(mitad.pasos.filter((p) => p.estado === 'lista')).toHaveLength(2);
    const lista = tareaPlanDemo(lote, DURACION_TAREA_MS);
    expect(lista.estado).toBe('lista');
    expect(lista.plan_id).not.toBeNull();
  });
});
