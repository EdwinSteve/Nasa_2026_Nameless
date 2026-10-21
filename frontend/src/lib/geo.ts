// src/lib/geo.ts
import type { GeoJSONPolygon } from '../api/tipos';

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
