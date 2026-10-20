// src/components/feedback/SatelliteScan.tsx
// Ilustración del satélite escaneando el lote. Las animaciones viven en globals.css.
import React, { useMemo } from 'react';
import type { GeoJSONPolygon } from '../../api/tipos';
import { formatearHectareas } from '../../lib/formato';

export interface SatelliteScanProps {
  nombreLote: string;
  areaHa: number;
  poligono?: GeoJSONPolygon | null;
  etiquetaSatelite?: string;
  estaEscaneando?: boolean;
}

type Punto = [number, number];

// Forma genérica si no hay polígono válido
const PUNTOS_POR_DEFECTO: Punto[] = [[120, 185], [240, 175], [275, 225], [180, 245], [95, 220]];

// Caja del "suelo" en el SVG: el lote se aplana en vertical para dar perspectiva
const SUELO = { x: 70, ancho: 220, yBase: 240, alto: 70 };

function proyectarPoligono(poligono: GeoJSONPolygon | null | undefined): Punto[] {
  const anillo = poligono?.coordinates[0];
  if (!anillo || anillo.length < 4) return PUNTOS_POR_DEFECTO;

  // El último punto repite el primero en GeoJSON: no se dibuja dos veces
  const vertices = anillo.slice(0, -1);
  const lngs = vertices.map(([lng]) => lng);
  const lats = vertices.map(([, lat]) => lat);
  const minLng = Math.min(...lngs);
  const minLat = Math.min(...lats);
  const spanLng = Math.max(...lngs) - minLng || 0.001;
  const spanLat = Math.max(...lats) - minLat || 0.001;

  return vertices.map(([lng, lat]) => [
    SUELO.x + ((lng - minLng) / spanLng) * SUELO.ancho,
    SUELO.yBase - ((lat - minLat) / spanLat) * SUELO.alto
  ]);
}

export const SatelliteScan: React.FC<SatelliteScanProps> = ({
  nombreLote,
  areaHa,
  poligono,
  etiquetaSatelite = 'Satélites de la NASA',
  estaEscaneando = true
}) => {
  const puntos = useMemo(() => proyectarPoligono(poligono), [poligono]);
  const puntosSvg = puntos.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const anim = (clase: string) => (estaEscaneando ? clase : undefined);

  return (
    <div className="relative w-full overflow-hidden rounded-3xl bg-[#EBF3FC] border border-[#D5E3F5] shadow-sm p-4 pt-5 pb-4 flex flex-col items-center justify-between">
      <div className="relative w-full max-w-[340px] h-[210px] flex items-center justify-center">
        <svg viewBox="0 0 360 260" className="w-full h-full select-none" fill="none" aria-hidden="true">
          <defs>
            <linearGradient id="hazGradiente" x1="180" y1="48" x2="180" y2="250" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#6DBE7A" stopOpacity="0.8" />
              <stop offset="35%" stopColor="#6DBE7A" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#6DBE7A" stopOpacity="0.08" />
            </linearGradient>
            <linearGradient id="terrenoGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#6DBE7A" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#1F4D2B" stopOpacity="0.25" />
            </linearGradient>
            <pattern id="gridCuadricula" width="16" height="16" patternUnits="userSpaceOnUse">
              <path d="M 16 0 L 0 0 0 16" fill="none" stroke="#6DBE7A" strokeWidth="0.6" strokeOpacity="0.4" />
            </pattern>
          </defs>

          {/* Elipses orbitales de perspectiva */}
          <ellipse cx="180" cy="205" rx="140" ry="46" stroke="#4A90C8" strokeWidth="1" strokeDasharray="4 3" strokeOpacity="0.35" />
          <ellipse cx="180" cy="205" rx="100" ry="32" stroke="#6DBE7A" strokeWidth="1.2" strokeOpacity="0.45" />
          <ellipse cx="180" cy="205" rx="60" ry="19" stroke="#6DBE7A" strokeWidth="1.2" strokeOpacity="0.6" />
          {estaEscaneando && (
            <ellipse cx="180" cy="205" rx="100" ry="32" stroke="#6DBE7A" strokeWidth="1.5" className="anim-onda" />
          )}

          {/* Lote proyectado */}
          <polygon points={puntosSvg} fill="url(#terrenoGrad)" stroke="#1F4D2B" strokeWidth="2" strokeDasharray="3 2" />
          <polygon points={puntosSvg} fill="url(#gridCuadricula)" />
          {puntos.map(([cx, cy], i) => (
            <circle key={i} cx={cx} cy={cy} r="3" fill="#E8833A" stroke="#FFFFFF" strokeWidth="1.5" />
          ))}

          {/* Haz de barrido */}
          <g className={anim('anim-haz')}>
            <polygon points="180,48 50,248 310,248" fill="url(#hazGradiente)" />
            <line x1="180" y1="48" x2="50" y2="248" stroke="#6DBE7A" strokeWidth="1.2" strokeOpacity="0.5" strokeDasharray="3 3" />
            <line x1="180" y1="48" x2="310" y2="248" stroke="#6DBE7A" strokeWidth="1.2" strokeOpacity="0.5" strokeDasharray="3 3" />
          </g>

          <path d="M 40 54 Q 180 20 320 54" stroke="#4A90C8" strokeWidth="1.2" strokeDasharray="4 4" strokeOpacity="0.45" />

          {/* Satélite genérico (sin logos) */}
          <g className={anim('anim-satelite')}>
            <circle cx="180" cy="40" r="28" fill="#1F4D2B" />
            <g transform="translate(166, 26)">
              <rect x="10" y="10" width="8" height="8" rx="1.5" fill="#FFFFFF" />
              <rect x="2" y="12" width="6" height="4" rx="0.8" fill="#E8833A" stroke="#FFFFFF" strokeWidth="0.8" />
              <rect x="20" y="12" width="6" height="4" rx="0.8" fill="#E8833A" stroke="#FFFFFF" strokeWidth="0.8" />
              <line x1="14" y1="18" x2="14" y2="22" stroke="#6DBE7A" strokeWidth="1.5" strokeLinecap="round" />
            </g>
            <circle cx="180" cy="48" r="3" fill="#6DBE7A" />
            <circle cx="180" cy="48" r="8" stroke="#6DBE7A" strokeWidth="1.2" className={anim('anim-onda')} />
          </g>
        </svg>
      </div>

      {/* Fuente que se está consultando */}
      <div className="absolute top-2.5 left-1/2 -translate-x-1/2 bg-white/95 backdrop-blur-sm border border-[#D5E3F5] px-3.5 py-1 rounded-full shadow-sm flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full bg-[#1F4D2B] ${estaEscaneando ? 'animate-pulse' : ''}`} />
        <span className="text-[11px] sm:text-xs font-black tracking-wide text-[#14202B]">{etiquetaSatelite}</span>
      </div>

      {/* Lote y área */}
      <div className="-mt-2.5 z-10 bg-white border border-[#D5E3F5] rounded-full py-1.5 px-4 shadow-sm flex items-center gap-2.5">
        <svg className="w-4 h-4 text-[#1F4D2B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 21V11M12 11C12 7 8 5 4 5C4 9 7 11 12 11ZM12 11C12 7 16 5 20 5C20 9 17 11 12 11Z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21H17" />
        </svg>
        <span className="text-sm font-extrabold text-[#14202B]">{nombreLote}</span>
        <span className="bg-[#B9E9B3] text-[#164321] text-xs font-black px-2.5 py-0.5 rounded-full">
          {formatearHectareas(areaHa)} ha
        </span>
      </div>
    </div>
  );
};
