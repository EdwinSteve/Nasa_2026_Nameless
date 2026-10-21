// De dónde sale un dato. Es el único lugar donde van los nombres técnicos (NASA SMAP, NASA POWER...).
import type { Procedencia } from '../../api/tipos';
import { formatearFechaCorta } from '../../lib/fechas';
import { IconoSatelite } from '../iconos/Iconos';

export function ChipFuente({ procedencia }: { procedencia: Procedencia }) {
  const texto = procedencia.fecha ? `${procedencia.fuente} · ${formatearFechaCorta(procedencia.fecha)}` : procedencia.fuente;
  return (
    <span className="inline-flex min-h-8 items-center gap-1.5 rounded-full bg-[#EAF1FB] px-3 text-sm font-semibold text-tinta">
      <IconoSatelite tamano={16} className="shrink-0 text-agua" />
      <span className="sr-only">Fuente: </span>
      {texto}
    </span>
  );
}
