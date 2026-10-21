import { describe, expect, it } from 'vitest';
import {
  formatearDiaMes,
  formatearEntero,
  formatearFechaCorta,
  formatearFechaLarga,
  formatearMesCorto,
  formatearUnDecimal,
  saludo
} from './fechas';

describe('saludo según la hora', () => {
  it.each([
    [5, 'Buenos días'],
    [11, 'Buenos días'],
    [12, 'Buenas tardes'],
    [18, 'Buenas tardes'],
    [19, 'Buenas noches'],
    [0, 'Buenas noches'],
    [4, 'Buenas noches']
  ])('a las %i h dice "%s"', (hora, esperado) => {
    expect(saludo(new Date(2026, 9, 14, hora, 30))).toBe(esperado);
  });
});

describe('formatos es-CO', () => {
  it('fecha larga con día de la semana', () => {
    expect(formatearFechaLarga(new Date(2026, 9, 14, 9))).toBe('miércoles, 14 de octubre');
  });

  it('fechas ISO del backend sin correrse un día por la zona horaria', () => {
    expect(formatearFechaCorta('2026-10-12')).toBe('12 oct');
    expect(formatearDiaMes('2027-01-20')).toBe('20 de enero');
  });

  it('meses de las gráficas con mayúscula inicial', () => {
    expect(formatearMesCorto('2026-05')).toBe('May');
    expect(formatearMesCorto('2026-10')).toBe('Oct');
  });

  it('miles con punto y decimales con coma', () => {
    expect(formatearEntero(1840)).toBe('1.840');
    expect(formatearEntero(20000)).toBe('20.000');
    expect(formatearUnDecimal(6.4)).toBe('6,4');
  });
});
