import { describe, expect, it } from 'vitest';
import { puntosLinea, techoEje, xCentros, yDe } from './graficas';

describe('escalas de las gráficas', () => {
  it('el techo del eje es redondo y deja margen sobre el máximo', () => {
    expect(techoEje([510, 480, 360])).toBe(600);
    expect(techoEje([72, 63])).toBe(100);   // 79,2 con el margen: paso de 50
    expect(techoEje([0, 0])).toBe(1);
  });

  it('el valor máximo queda arriba y el cero abajo', () => {
    expect(yDe(600, 600, 140)).toBe(0);
    expect(yDe(0, 600, 140)).toBe(140);
    expect(yDe(-5, 600, 140)).toBe(140); // nunca por debajo del eje
  });

  it('las barras quedan centradas en partes iguales', () => {
    expect(xCentros(3, 300)).toEqual([50, 150, 250]);
    expect(xCentros(0, 300)).toEqual([]);
  });

  it('la línea va de un borde al otro', () => {
    expect(puntosLinea([63, 72], 300, 100, 63, 72)).toBe('0.0,100.0 300.0,0.0');
    expect(puntosLinea([70], 300, 100, 60, 80)).toBe('150.0,50.0');
  });
});
