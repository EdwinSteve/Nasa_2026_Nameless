// src/lib/graficas.ts
// Escalas de las gráficas SVG propias de la pantalla Inicio.

/** Techo "redondo" del eje: el siguiente múltiplo de 50 o 100 por encima del máximo, con margen. */
export function techoEje(valores: number[], margen = 1.1): number {
  const maximo = Math.max(0, ...valores) * margen;
  if (maximo === 0) return 1;
  const paso = maximo > 300 ? 100 : maximo > 50 ? 50 : 10;
  return Math.ceil(maximo / paso) * paso;
}

/** Posición vertical (0 arriba) de un valor en un alto dado, con el techo del eje. */
export function yDe(valor: number, techo: number, alto: number): number {
  return alto - (Math.max(0, valor) / techo) * alto;
}

/** Posiciones horizontales centradas de n elementos en un ancho dado. */
export function xCentros(n: number, ancho: number): number[] {
  if (n === 0) return [];
  const paso = ancho / n;
  return Array.from({ length: n }, (_, i) => paso * i + paso / 2);
}

/** Puntos de una línea SVG ("x,y x,y ...") para una serie de valores. */
export function puntosLinea(valores: number[], ancho: number, alto: number, minimo: number, maximo: number): string {
  const xs = valores.length === 1 ? [ancho / 2] : valores.map((_, i) => (i / (valores.length - 1)) * ancho);
  const rango = maximo - minimo || 1;
  return valores.map((v, i) => `${xs[i].toFixed(1)},${(alto - ((v - minimo) / rango) * alto).toFixed(1)}`).join(' ');
}
