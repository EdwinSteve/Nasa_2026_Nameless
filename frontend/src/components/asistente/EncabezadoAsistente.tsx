// "Asistente SURCO" y, debajo, con qué lote responde (se toca para cambiarlo).
'use client';

import { useId } from 'react';
import type { LoteResumen } from '../../api/tipos';
import { formatearUnDecimal } from '../../lib/fechas';
import { IconoChevron } from '../iconos/Iconos';
import { AvatarAsistente } from './AvatarAsistente';

interface Props {
  lotes: LoteResumen[];
  loteId: string | null;
  onCambiarLote: (loteId: string) => void;
}

export function EncabezadoAsistente({ lotes, loteId, onCambiarLote }: Props) {
  const id = useId();
  const lote = lotes.find((l) => l.id === loteId);
  const texto = lote ? `Le respondo con los datos de su lote ${lote.nombre}` : 'Le respondo con los datos de su lote';

  return (
    <header className="flex items-center gap-3 border-b border-borde/70 bg-white px-4 py-2 lg:px-6">
      <AvatarAsistente tamano="grande" />
      <div className="min-w-0 flex-1">
        <h1 className="font-titulo text-xl font-extrabold leading-tight text-tinta">Asistente SURCO</h1>
        {lotes.length > 1 && lote ? (
          // El select nativo va encima del texto, invisible: se toca el texto y se abre la lista de lotes
          <div className="relative flex min-h-14 min-w-0 items-center">
            <span aria-hidden="true" className="flex min-w-0 items-center gap-1 text-base text-campo">
              <span className="leading-snug underline decoration-campo/40 underline-offset-4">{texto}</span>
              <IconoChevron tamano={18} className="shrink-0" />
            </span>
            <label htmlFor={id} className="sr-only">
              Lote con el que le responde el asistente
            </label>
            <select
              id={id}
              value={lote.id}
              onChange={(e) => onCambiarLote(e.target.value)}
              className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
            >
              {lotes.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.nombre} · {formatearUnDecimal(l.area_ha)} ha
                </option>
              ))}
            </select>
          </div>
        ) : (
          <p className="flex min-h-14 items-center text-base text-tinta/75">{texto}</p>
        )}
      </div>
    </header>
  );
}
