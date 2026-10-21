// Selector del lote al que se le muestra el plan: "La Vega · 6,4 ha".
'use client';

import { useId } from 'react';
import type { LoteResumen } from '../../api/tipos';
import { formatearUnDecimal } from '../../lib/fechas';
import { IconoChevron, IconoUbicacion } from '../iconos/Iconos';

const etiqueta = (l: LoteResumen) => `${l.nombre} · ${formatearUnDecimal(l.area_ha)} ha`;

interface Props {
  lotes: LoteResumen[];
  loteId: string | null;
  onCambiar: (loteId: string) => void;
}

export function SelectorLote({ lotes, loteId, onCambiar }: Props) {
  const id = useId();
  const actual = lotes.find((l) => l.id === loteId);
  if (!actual) return null;

  if (lotes.length === 1) {
    return (
      <p className="inline-flex min-h-12 items-center gap-2 rounded-full bg-white px-4 text-base font-bold text-tinta shadow-sm">
        <IconoUbicacion tamano={20} className="text-sol" />
        {etiqueta(actual)}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-semibold text-tinta/75">
        Lote
      </label>
      <div className="relative w-full max-w-sm">
        <IconoUbicacion tamano={20} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sol" />
        <select
          id={id}
          value={actual.id}
          onChange={(e) => onCambiar(e.target.value)}
          className="min-h-12 w-full appearance-none rounded-full border-2 border-borde bg-white pl-11 pr-11 text-base font-bold text-tinta shadow-sm focus:border-campo focus:outline-none"
        >
          {lotes.map((l) => (
            <option key={l.id} value={l.id}>
              {etiqueta(l)}
            </option>
          ))}
        </select>
        <IconoChevron tamano={20} className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-tinta/60" />
      </div>
    </div>
  );
}
