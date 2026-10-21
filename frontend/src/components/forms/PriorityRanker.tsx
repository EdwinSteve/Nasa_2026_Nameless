// src/components/forms/PriorityRanker.tsx
import React from 'react';
import type { PrioridadTipo } from '../../api/tipos';

const PRIORIDAD_INFO: Record<PrioridadTipo, { titulo: string; descripcion: string }> = {
  ahorro_agua: {
    titulo: 'Ahorrar agua',
    descripcion: 'Cultivos y fechas que necesitan menos riego.'
  },
  ganar_mas: {
    titulo: 'Ganar más',
    descripcion: 'Cultivos con mejor precio y rendimiento esperado.'
  },
  cuidar_suelo: {
    titulo: 'Cuidar el suelo',
    descripcion: 'Rotaciones que devuelven nutrientes a la tierra.'
  },
  arriesgar_menos: {
    titulo: 'Arriesgar menos',
    descripcion: 'Opciones más seguras ante sequías o lluvias fuertes.'
  }
};

export interface PriorityRankerProps {
  id?: string;
  orden: PrioridadTipo[];
  onChange: (orden: PrioridadTipo[]) => void;
  label?: string;
  disabled?: boolean;
}

export const PriorityRanker: React.FC<PriorityRankerProps> = ({
  id = 'ordenar-prioridades',
  orden,
  onChange,
  label = 'Ordena lo que más te importa',
  disabled = false
}) => {
  const mover = (indice: number, direccion: -1 | 1) => {
    const destino = indice + direccion;
    if (destino < 0 || destino >= orden.length) return;
    const nuevo = [...orden];
    [nuevo[indice], nuevo[destino]] = [nuevo[destino], nuevo[indice]];
    onChange(nuevo);
  };

  return (
    <fieldset id={id} className="w-full text-left border-none p-0 m-0" disabled={disabled}>
      <legend className="text-base sm:text-lg font-bold text-[#14202B] mb-1 block">{label}</legend>
      <p className="text-sm text-[#14202B]/70 mb-3">
        La primera es la más importante para ti. Usa las flechas para subir o bajar cada una.
      </p>

      <ol className="space-y-3">
        {orden.map((prioridad, i) => {
          const info = PRIORIDAD_INFO[prioridad];
          return (
            <li
              key={prioridad}
              className={`flex items-center gap-3 p-3 rounded-xl border-2 bg-white ${
                i === 0 ? 'border-[#1F4D2B] ring-1 ring-[#1F4D2B]' : 'border-[#D2C8B5]'
              }`}
            >
              <span
                aria-hidden="true"
                className={`w-10 h-10 shrink-0 rounded-full flex items-center justify-center text-lg font-black ${
                  i === 0 ? 'bg-[#1F4D2B] text-white' : 'bg-[#E8E1D3] text-[#14202B]'
                }`}
              >
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <span className="block text-base font-extrabold text-[#14202B]">{info.titulo}</span>
                <span className="block text-sm text-[#14202B]/70">{info.descripcion}</span>
              </div>
              <div className="flex flex-col gap-1">
                <button
                  type="button"
                  onClick={() => mover(i, -1)}
                  disabled={disabled || i === 0}
                  aria-label={`Subir ${info.titulo}`}
                  className="min-w-[56px] min-h-[28px] rounded-lg border-2 border-[#D2C8B5] text-[#1F4D2B] font-black disabled:opacity-30 hover:border-[#1F4D2B]"
                >
                  ▲
                </button>
                <button
                  type="button"
                  onClick={() => mover(i, 1)}
                  disabled={disabled || i === orden.length - 1}
                  aria-label={`Bajar ${info.titulo}`}
                  className="min-w-[56px] min-h-[28px] rounded-lg border-2 border-[#D2C8B5] text-[#1F4D2B] font-black disabled:opacity-30 hover:border-[#1F4D2B]"
                >
                  ▼
                </button>
              </div>
            </li>
          );
        })}
      </ol>
    </fieldset>
  );
};
