import { describe, expect, it } from 'vitest';
import { resumenDemo, ultimosMeses } from './inicio';

const HOY = new Date(2026, 9, 14, 9);

describe('mock de GET /inicio', () => {
  it('los meses salen de la fecha de hoy, no son fijos', () => {
    expect(ultimosMeses(3, HOY)).toEqual(['2026-08', '2026-09', '2026-10']);
    expect(ultimosMeses(2, new Date(2027, 0, 5))).toEqual(['2026-12', '2027-01']);
  });

  it('con historia: logros, series de 6 y 12 meses y cosecha estimada desde hoy', () => {
    const r = resumenDemo('historia', HOY);
    expect(r.logros?.frecuencia_exito).toBe(8);
    expect(r.series?.agua_mensual.map((m) => m.mes)).toEqual(ultimosMeses(6, HOY));
    expect(r.series?.salud_suelo).toHaveLength(12);
    expect(r.lote_principal?.cultivo?.fecha_cosecha_estimada).toBe('2026-12-19'); // hoy + 66 días
  });

  it('de noche las fechas siguen siendo las de hoy en Colombia, no las de UTC', () => {
    const r = resumenDemo('historia', new Date(2026, 9, 20, 21));
    expect(r.clima_hoy.procedencia.fecha).toBe('2026-10-20');
    expect(r.recomendacion_hoy?.procedencia.fecha).toBe('2026-10-18');
  });

  it('usuario nuevo: sin logros ni series, pero con lote', () => {
    const r = resumenDemo('nuevo', HOY);
    expect(r.logros).toBeNull();
    expect(r.series).toBeNull();
    expect(r.lote_principal?.cultivo).toBeNull();
  });

  it('sin lote', () => {
    expect(resumenDemo('sin-lote', HOY).lote_principal).toBeNull();
  });
});
