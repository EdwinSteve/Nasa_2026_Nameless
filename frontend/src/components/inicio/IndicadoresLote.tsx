// Humedad de la tierra, verdor del cultivo y calor, en palabras sencillas. La fuente técnica va en el chip.
import type { ComponentType } from 'react';
import type { EstadoSimple, ResumenInicio } from '../../api/tipos';
import { IconoGota, IconoHoja, IconoTermometro } from '../iconos/Iconos';
import { ChipFuente } from './ChipFuente';

const COLOR: Record<EstadoSimple['nivel'], string> = {
  bueno: 'bg-hoja/25 text-campo',
  regular: 'bg-sol/15 text-[#9A4A12]',
  malo: 'bg-[#D94F4F]/15 text-[#A33333]',
  sin_dato: 'bg-[#E8E1D3] text-tinta/75'
};

type Indicadores = NonNullable<ResumenInicio['lote_principal']>['indicadores'];

const FILAS: { clave: keyof Indicadores; nombre: string; Icono: ComponentType<{ tamano?: number; className?: string }> }[] = [
  { clave: 'humedad', nombre: 'Humedad de la tierra', Icono: IconoGota },
  { clave: 'verdor', nombre: 'Verdor del cultivo', Icono: IconoHoja },
  { clave: 'calor', nombre: 'Calor', Icono: IconoTermometro }
];

export function IndicadoresLote({ indicadores }: { indicadores: Indicadores }) {
  return (
    <ul className="flex flex-col gap-2" aria-label="Cómo está su lote">
      {FILAS.map(({ clave, nombre, Icono }) => {
        const estado = indicadores[clave];
        return (
          <li key={clave} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border-2 border-[#EFE9DD] bg-white px-4 py-3">
            <span className="flex items-center gap-2 text-base font-semibold text-tinta">
              <Icono tamano={22} className="text-campo" />
              {nombre}
            </span>
            <span className="flex flex-wrap items-center gap-2">
              <span className={`rounded-full px-3 py-1 text-sm font-bold ${COLOR[estado.nivel]}`}>{estado.etiqueta}</span>
              {estado.procedencia && <ChipFuente procedencia={estado.procedencia} />}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
