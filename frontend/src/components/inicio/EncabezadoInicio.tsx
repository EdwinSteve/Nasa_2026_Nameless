// Saludo según la hora, fecha de hoy, clima y la ÚNICA campana de alertas de la pantalla.
import Link from 'next/link';
import type { ResumenInicio } from '../../api/tipos';
import { formatearEntero, formatearFechaLarga, saludo } from '../../lib/fechas';
import { IconoCampana, IconoLluvia, IconoNube, IconoSol } from '../iconos/Iconos';
import { ChipFuente } from './ChipFuente';

const CLIMA = {
  soleado: { texto: 'Soleado', Icono: IconoSol, color: 'text-sol' },
  nublado: { texto: 'Nublado', Icono: IconoNube, color: 'text-tinta/70' },
  lluvia: { texto: 'Lluvia', Icono: IconoLluvia, color: 'text-agua' }
} as const;

interface Props {
  nombre: string;
  ahora: Date;
  clima: ResumenInicio['clima_hoy'];
  alertas: number;
}

export function EncabezadoInicio({ nombre, ahora, clima, alertas }: Props) {
  const { texto, Icono, color } = CLIMA[clima.estado];
  return (
    <header className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-titulo text-base font-extrabold text-campo">SURCO</p>
          <h1 className="font-titulo text-[28px] font-black leading-tight text-tinta lg:text-4xl">
            {saludo(ahora)}, {nombre}
          </h1>
          <p className="text-base text-tinta/75 first-letter:uppercase">{formatearFechaLarga(ahora)}</p>
        </div>
        <Link
          href="/alertas"
          aria-label={alertas ? `Ver ${alertas} ${alertas === 1 ? 'alerta pendiente' : 'alertas pendientes'}` : 'Ver alertas'}
          className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-white text-tinta shadow-sm hover:text-campo"
        >
          <IconoCampana tamano={26} />
          {alertas > 0 && (
            <span
              aria-hidden="true"
              className="absolute top-1.5 right-1.5 flex h-6 min-w-6 items-center justify-center rounded-full bg-sol px-1 text-sm font-bold text-white"
            >
              {alertas}
            </span>
          )}
        </Link>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <p className="inline-flex min-h-11 items-center gap-2 rounded-full bg-white px-4 text-base font-semibold text-tinta shadow-sm">
          <Icono tamano={22} className={color} />
          {formatearEntero(clima.temperatura_c)} °C · {texto} · {formatearEntero(clima.probabilidad_lluvia_pct)} % de lluvia
        </p>
        <ChipFuente procedencia={clima.procedencia} />
      </div>
    </header>
  );
}
