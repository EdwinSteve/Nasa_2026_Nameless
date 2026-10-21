// src/components/forms/MapDrawer.tsx
// Marcador de posición del mapa: el modo "dibujar" se conectará a Leaflet.
import React, { useState } from 'react';
import type { GeoJSONPolygon } from '../../api/tipos';

export type MapMode = 'dibujar' | 'caminar_borde' | 'coordenadas';

export interface MapDrawerProps {
  id?: string;
  poligono: GeoJSONPolygon | null;
  area_ha: number | null;
  modo: MapMode;
  onModoChange: (modo: MapMode) => void;
  onPolygonChange: (poligono: GeoJSONPolygon | null) => void;
  error?: string;
  disabled?: boolean;
}

export const MapDrawer: React.FC<MapDrawerProps> = ({
  id = 'map-drawer-lote',
  poligono,
  area_ha,
  modo,
  onModoChange,
  onPolygonChange,
  error,
  disabled = false
}) => {
  // Coordenadas con valores iniciales VACÍOS
  const [latInput, setLatInput] = useState<string>('');
  const [lngInput, setLngInput] = useState<string>('');
  const [radioMetros, setRadioMetros] = useState<string>('100');
  const [coordError, setCoordError] = useState<string | null>(null);

  const handleApplyCoordinates = () => {
    setCoordError(null);
    const latClean = latInput.replace(',', '.').trim();
    const lngClean = lngInput.replace(',', '.').trim();
    const radioClean = radioMetros.replace(',', '.').trim();

    if (!latClean || !lngClean) {
      setCoordError('Debes ingresar latitud y longitud.');
      return;
    }

    const lat = parseFloat(latClean);
    const lng = parseFloat(lngClean);
    const radio = parseFloat(radioClean) || 100;

    // Validación estricta de coordenadas para Colombia (-4.3 a 13.5 lat, -82 a -66 lng)
    if (isNaN(lat) || lat < -4.3 || lat > 13.5) {
      setCoordError('La latitud debe estar dentro de Colombia (entre -4.3 y 13.5).');
      return;
    }

    if (isNaN(lng) || lng < -82.0 || lng > -66.0) {
      setCoordError('La longitud debe estar dentro de Colombia (entre -82.0 y -66.0).');
      return;
    }

    // Delta aproximado para calcular bounding box del radio en metros
    const delta = radio / 111320;
    const box: GeoJSONPolygon = {
      type: 'Polygon',
      coordinates: [[
        [lng - delta, lat - delta],
        [lng + delta, lat - delta],
        [lng + delta, lat + delta],
        [lng - delta, lat + delta],
        [lng - delta, lat - delta]
      ]]
    };
    onPolygonChange(box);
  };

  return (
    <div id={id} className="w-full flex flex-col space-y-4 text-left">
      {/* Selector de modo táctil de 56px de altura */}
      <div className="grid grid-cols-3 gap-2 bg-[#E8E1D3] p-1.5 rounded-2xl">
        <button
          type="button"
          disabled={disabled}
          aria-pressed={modo === 'dibujar'}
          onClick={() => onModoChange('dibujar')}
          className={`min-h-[56px] py-2 px-1 text-xs sm:text-sm font-extrabold rounded-xl transition-all flex flex-col items-center justify-center gap-1 ${
            modo === 'dibujar'
              ? 'bg-[#1F4D2B] text-white shadow-md'
              : 'text-[#14202B]/80 hover:bg-white/60'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
          <span>Tocar esquinas</span>
        </button>

        <button
          type="button"
          disabled={disabled}
          aria-pressed={modo === 'caminar_borde'}
          onClick={() => onModoChange('caminar_borde')}
          className={`min-h-[56px] py-2 px-1 text-xs sm:text-sm font-extrabold rounded-xl transition-all flex flex-col items-center justify-center gap-1 ${
            modo === 'caminar_borde'
              ? 'bg-[#1F4D2B] text-white shadow-md'
              : 'text-[#14202B]/80 hover:bg-white/60'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span>Caminar el borde</span>
        </button>

        <button
          type="button"
          disabled={disabled}
          aria-pressed={modo === 'coordenadas'}
          onClick={() => onModoChange('coordenadas')}
          className={`min-h-[56px] py-2 px-1 text-xs sm:text-sm font-extrabold rounded-xl transition-all flex flex-col items-center justify-center gap-1 ${
            modo === 'coordenadas'
              ? 'bg-[#1F4D2B] text-white shadow-md'
              : 'text-[#14202B]/80 hover:bg-white/60'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          </svg>
          <span>Coordenadas</span>
        </button>
      </div>

      {/* Contenedor id="mapa-lote" */}
      <div
        id="mapa-lote"
        className="relative w-full h-72 sm:h-80 bg-[#1D3323] rounded-2xl overflow-hidden border-2 border-[#1F4D2B] shadow-inner flex flex-col justify-between p-4"
      >
        <div
          className="absolute inset-0 opacity-40 bg-cover bg-center pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle at 50% 50%, rgba(109, 190, 122, 0.3) 0%, rgba(20, 32, 43, 0.9) 100%)`
          }}
        />

        {!poligono && modo === 'dibujar' && (
          <div className="relative z-10 m-auto bg-black/75 backdrop-blur-sm px-5 py-3 rounded-xl border border-white/20 text-center">
            <p className="text-white text-base font-bold">
              Toca las esquinas de tu lote
            </p>
            <span className="text-xs text-white/70 mt-0.5 block">
              Haz clic en cada vértice para cerrar el perímetro
            </span>
          </div>
        )}

        {modo === 'caminar_borde' && (
          <div className="relative z-10 m-auto bg-white/95 backdrop-blur-md p-4 rounded-xl text-center shadow-lg max-w-xs">
            <p className="text-sm font-bold text-[#14202B]">
              Caminarás el lindero con el celular en la mano
            </p>
            <p className="text-xs text-[#14202B]/70 mt-1 mb-3">
              La captura GPS registrará los puntos conforme rodees el predio.
            </p>
            <button
              type="button"
              disabled={disabled}
              onClick={() => {
                onPolygonChange({
                  type: 'Polygon',
                  coordinates: [[
                    [-75.2941, 2.9912],
                    [-75.2895, 2.9920],
                    [-75.2882, 2.9865],
                    [-75.2930, 2.9858],
                    [-75.2941, 2.9912]
                  ]]
                });
              }}
              className="w-full min-h-[56px] bg-[#1F4D2B] hover:bg-[#16381F] text-white rounded-xl font-bold text-base transition-all"
            >
              Simular recorrido (demo)
            </button>
          </div>
        )}

        {modo === 'coordenadas' && (
          <div className="relative z-10 m-auto bg-white/95 backdrop-blur-md p-4 rounded-xl shadow-lg w-full max-w-sm">
            <div className="grid grid-cols-2 gap-3 mb-2">
              <div>
                <label htmlFor="coord-lat" className="text-base font-bold text-[#14202B] block mb-1">
                  Latitud
                </label>
                <input
                  id="coord-lat"
                  type="text"
                  value={latInput}
                  onChange={(e) => setLatInput(e.target.value)}
                  placeholder="Ej: 2.9912"
                  disabled={disabled}
                  className="w-full min-h-[56px] h-14 px-3 border-2 border-[#D2C8B5] rounded-xl text-base font-mono font-bold text-[#14202B]"
                />
              </div>
              <div>
                <label htmlFor="coord-lng" className="text-base font-bold text-[#14202B] block mb-1">
                  Longitud
                </label>
                <input
                  id="coord-lng"
                  type="text"
                  value={lngInput}
                  onChange={(e) => setLngInput(e.target.value)}
                  placeholder="Ej: -75.2941"
                  disabled={disabled}
                  className="w-full min-h-[56px] h-14 px-3 border-2 border-[#D2C8B5] rounded-xl text-base font-mono font-bold text-[#14202B]"
                />
              </div>
            </div>

            <div className="mb-3">
              <label htmlFor="coord-radio" className="text-base font-bold text-[#14202B] block mb-1">
                Radio en metros
              </label>
              <input
                id="coord-radio"
                type="text"
                value={radioMetros}
                onChange={(e) => setRadioMetros(e.target.value)}
                placeholder="100"
                disabled={disabled}
                className="w-full min-h-[56px] h-14 px-3 border-2 border-[#D2C8B5] rounded-xl text-base font-bold text-[#14202B]"
              />
            </div>

            {coordError && (
              <span aria-live="polite" className="text-xs font-bold text-[#D94F4F] block mb-2">
                {coordError}
              </span>
            )}

            <button
              type="button"
              disabled={disabled}
              onClick={handleApplyCoordinates}
              className="w-full min-h-[56px] bg-[#1F4D2B] hover:bg-[#16381F] text-white rounded-xl font-bold text-base transition-all"
            >
              Usar estas coordenadas
            </button>
          </div>
        )}

        {/* Badge inferior: Cálculo de Área */}
        <div className="relative z-10 bg-white/95 rounded-xl p-3 shadow-md flex items-center justify-between">
          <div>
            <span className="text-xs text-[#14202B]/60 font-bold block uppercase tracking-wider">
              Área estimada del lote
            </span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-[#1F4D2B]">
                {area_ha !== null ? area_ha.toFixed(1) : '—'}
              </span>
              <span className="text-base font-bold text-[#14202B]">
                ha
              </span>
            </div>
          </div>
          {poligono && !disabled && (
            <button
              type="button"
              onClick={() => onPolygonChange(null)}
              className="text-xs font-bold text-[#D94F4F] bg-[#D94F4F]/10 px-3 py-2 rounded-lg border border-[#D94F4F]/20"
            >
              Borrar esquinas
            </button>
          )}
        </div>
      </div>

      {error && (
        <span aria-live="polite" className="text-sm font-semibold text-[#D94F4F] block">
          {error}
        </span>
      )}
    </div>
  );
};
