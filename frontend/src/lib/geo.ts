// src/lib/geo.ts
import type { Coordenada, GeoJSONPolygon } from '../api/tipos';

const RADIO_TIERRA_M = 6_371_008.8;

/**
 * Área aproximada en hectáreas de un polígono GeoJSON (EPSG:4326).
 * Proyección equirectangular local + fórmula del área de Gauss: error <1 %
 * para lotes de unas pocas hectáreas. El valor oficial lo calcula el backend.
 */
export function calcularAreaHa(poligono: GeoJSONPolygon): number {
  const anillo = poligono.coordinates[0] ?? [];
  if (anillo.length < 4) return 0;

  const latMedia = (anillo.reduce((suma, [, lat]) => suma + lat, 0) / anillo.length) * (Math.PI / 180);
  const aMetros = ([lng, lat]: number[]) => [
    lng * (Math.PI / 180) * RADIO_TIERRA_M * Math.cos(latMedia),
    lat * (Math.PI / 180) * RADIO_TIERRA_M
  ];

  let doble = 0;
  for (let i = 0; i < anillo.length - 1; i++) {
    const [x1, y1] = aMetros(anillo[i]);
    const [x2, y2] = aMetros(anillo[i + 1]);
    doble += x1 * y2 - x2 * y1;
  }
  return Math.abs(doble) / 2 / 10_000;
}

/**
 * Punto medio del lote: centroide ponderado por área, la misma fórmula del backend
 * (Poligono.centroide). Sirve para mostrarlo mientras el productor dibuja; el valor
 * que se guarda lo calcula el servidor.
 */
export function calcularCentroide(poligono: GeoJSONPolygon): Coordenada | null {
  const anillo = poligono.coordinates[0] ?? [];
  if (anillo.length < 4) return null;
  const vertices = anillo.slice(0, -1);
  const latMedia = (vertices.reduce((suma, [, lat]) => suma + lat, 0) / vertices.length) * (Math.PI / 180);
  const [lonRef, latRef] = anillo[0];
  const escalaX = (Math.PI / 180) * RADIO_TIERRA_M * Math.cos(latMedia);
  const escalaY = (Math.PI / 180) * RADIO_TIERRA_M;
  const puntos = anillo.map(([lon, lat]) => [(lon - lonRef) * escalaX, (lat - latRef) * escalaY]);

  let area2 = 0;
  let cx = 0;
  let cy = 0;
  for (let i = 0; i < puntos.length - 1; i++) {
    const [x1, y1] = puntos[i];
    const [x2, y2] = puntos[i + 1];
    const cruz = x1 * y2 - x2 * y1;
    area2 += cruz;
    cx += (x1 + x2) * cruz;
    cy += (y1 + y2) * cruz;
  }
  if (area2 === 0) return null;
  return { lat: latRef + cy / (3 * area2) / escalaY, lon: lonRef + cx / (3 * area2) / escalaX };
}

/** Cierra una lista de esquinas [lat, lon] en un polígono GeoJSON ([lon, lat], primera = última). */
export function esquinasAPoligono(esquinas: [number, number][]): GeoJSONPolygon {
  const anillo = esquinas.map(([lat, lon]) => [lon, lat]);
  return { type: 'Polygon', coordinates: [[...anillo, anillo[0]]] };
}

/** Esquinas [lat, lon] de un polígono GeoJSON, sin repetir el cierre. */
export function poligonoAEsquinas(poligono: GeoJSONPolygon): [number, number][] {
  return (poligono.coordinates[0] ?? []).slice(0, -1).map(([lon, lat]) => [lat, lon] as [number, number]);
}
