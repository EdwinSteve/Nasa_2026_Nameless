import { describe, expect, it } from 'vitest';
import type { CultivoRanking } from '../api/tipos';
import { planDemo } from '../api/mocks/plan';
import {
  formatearIp,
  lluviaEnPalabras,
  nombreCultivo,
  ordenarRanking,
  rotacionParaCultivo,
  tareaEnCurso,
  textoFrecuencia,
  textoLluvia,
  textoMejorEpoca,
  textoSiSiembra,
  textoTemperatura
} from './plan';

const cultivo = (cultivo_id: string, ip: number, apto = true): CultivoRanking => ({
  cultivo_id,
  nombre: cultivo_id,
  ip,
  apto,
  razon_no_apto: apto ? null : 'muy caliente'
});

describe('ranking de cultivos', () => {
  it('los aptos van primero de mayor a menor y los no aptos al final', () => {
    const orden = ordenarRanking([cultivo('cafe', 0.9, false), cultivo('soya', 0.56), cultivo('arroz', 0.83), cultivo('yuca', 0.1, false)]);
    expect(orden.map((c) => c.cultivo_id)).toEqual(['arroz', 'soya', 'cafe', 'yuca']);
  });

  it('el valor va con coma decimal y entre 0 y 1', () => {
    expect(formatearIp(0.83)).toBe('0,83');
    expect(formatearIp(1.4)).toBe('1,00');
  });
});

describe('textos del plan', () => {
  it('frecuencia en "N de cada 10", nunca en porcentaje', () => {
    expect(textoFrecuencia(8)).toBe('8 de cada 10 años le va bien');
  });

  it('mejor época dentro del mismo mes y entre dos meses', () => {
    expect(textoMejorEpoca('2027-03-08', '2027-03-22')).toBe('Mejor época: del 8 al 22 de marzo');
    expect(textoMejorEpoca('2027-02-25', '2027-03-10')).toBe('Mejor época: del 25 de febrero al 10 de marzo');
    expect(textoMejorEpoca('2027-03-08', '2027-03-08')).toBe('Mejor época: el 8 de marzo');
  });

  it('al tocar un punto de la gráfica', () => {
    expect(textoSiSiembra('2027-04-15', 5)).toBe('Si siembra el 15 de abril: 5 de cada 10 años');
  });

  it('los controles se leen en palabras', () => {
    expect(textoLluvia(-20)).toBe('20 % menos lluvia');
    expect(textoLluvia(0)).toBe('La lluvia de siempre');
    expect(textoLluvia(10)).toBe('10 % más lluvia');
    expect(textoTemperatura(0)).toBe('El calor de siempre');
    expect(textoTemperatura(1)).toBe('1 grado más de calor');
    expect(textoTemperatura(3)).toBe('3 grados más de calor');
  });

  it('la lluvia en palabras: sol si es seco y hasta tres gotas', () => {
    expect(lluviaEnPalabras({ nivel: 'seco', lluvia_mm: 40 })).toEqual({ texto: 'Poca lluvia', gotas: 0 });
    expect(lluviaEnPalabras({ nivel: 'normal', lluvia_mm: 90 }).gotas).toBe(1);
    expect(lluviaEnPalabras({ nivel: 'lluvioso', lluvia_mm: 190 })).toEqual({ texto: 'Muchas lluvias', gotas: 3 });
  });
});

describe('del plan al detalle', () => {
  const plan = planDemo('lote-1', new Date(2026, 9, 20));

  it('usa la rotación pedida si incluye el cultivo', () => {
    expect(rotacionParaCultivo(plan, 'maiz', 'rot-arroz-soya-maiz')?.id).toBe('rot-arroz-soya-maiz');
  });

  it('si no viene rotación, la mejor que incluya el cultivo; si ninguna lo tiene, null', () => {
    expect(rotacionParaCultivo(plan, 'mani', null)?.id).toBe('rot-sorgo-mani-maiz');
    expect(rotacionParaCultivo(plan, 'arroz_riego', 'rot-maiz-soya-sorgo')?.id).toBe('rot-arroz-soya-maiz');
    expect(rotacionParaCultivo(plan, 'cacao', null)).toBeNull();
  });

  it('el nombre sale del ranking o de las rotaciones', () => {
    expect(nombreCultivo(plan, 'cafe')).toBe('Café');
    expect(nombreCultivo(plan, 'mani')).toBe('Maní');
    expect(nombreCultivo(plan, 'papa')).toBeNull();
  });

  it('lee el tarea_id de un 409 PLAN_EN_CALCULO', () => {
    expect(tareaEnCurso({ codigo: 'PLAN_EN_CALCULO', mensaje: '', detalles: [{ campo: 'tarea_id', mensaje: 't-1' }] })).toBe('t-1');
    expect(tareaEnCurso({ codigo: 'PLAN_NO_DISPONIBLE', mensaje: '' })).toBeNull();
  });
});
