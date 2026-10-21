'use client';

// Chip de altitud con sus 4 estados: sin_permiso, cargando, con_dato, no_disponible.
import { useState } from 'react';
import type { EstadoAltitud } from '../../hooks/useAltitud';
import { IconoMontana } from '../iconos/Iconos';

export interface ChipAltitudProps {
  estado: EstadoAltitud;
  altitudTexto: string | null;
  onSolicitar: () => void;
}

const BASE = 'inline-flex min-h-11 items-center gap-1.5 rounded-full bg-white/92 px-3.5 text-tinta shadow-sm';

export function ChipAltitud({ estado, altitudTexto, onSolicitar }: ChipAltitudProps) {
  const [ayuda, setAyuda] = useState(false);

  return (
    <span className="relative">
      <span className="sr-only" aria-live="polite">
        {estado === 'cargando' ? 'Midiendo la altitud' : estado === 'con_dato' && altitudTexto ? `Altitud: ${altitudTexto}` : ''}
      </span>

      {estado === 'sin_permiso' && (
        <button type="button" onClick={onSolicitar} className={`${BASE} hover:bg-white`}>
          <IconoMontana tamano={18} className="text-campo" />
          <span className="whitespace-nowrap text-sm font-semibold">Ver mi altitud</span>
        </button>
      )}

      {estado === 'cargando' && (
        <span className={BASE}>
          <IconoMontana tamano={18} className="text-campo" />
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-campo/25 border-t-campo motion-reduce:animate-none" aria-hidden="true" />
          <span className="whitespace-nowrap text-sm font-semibold">Midiendo…</span>
        </span>
      )}

      {estado === 'con_dato' && altitudTexto && (
        <>
          <button
            type="button"
            onClick={() => setAyuda((v) => !v)}
            aria-expanded={ayuda}
            aria-describedby={ayuda ? 'ayuda-altitud' : undefined}
            className={`${BASE} hover:bg-white`}
          >
            <IconoMontana tamano={18} className="text-campo" />
            <span className="whitespace-nowrap font-titulo text-sm font-extrabold">{altitudTexto}</span>
          </button>
          {ayuda && (
            <span id="ayuda-altitud" role="tooltip" className="absolute right-0 bottom-full mb-2 whitespace-nowrap rounded-xl bg-tinta px-3 py-1.5 text-sm text-white shadow-lg">
              Calculado con su ubicación
            </span>
          )}
        </>
      )}
    </span>
  );
}
