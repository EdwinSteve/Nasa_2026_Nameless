// Salud del suelo mes a mes (línea), en SVG propio.
import { useId } from 'react';
import type { ResumenInicio } from '../../api/tipos';
import { formatearEntero, formatearMesAnio, formatearMesCorto } from '../../lib/fechas';
import { puntosLinea } from '../../lib/graficas';

const ANCHO = 300;
const ALTO = 100;

type Fila = NonNullable<ResumenInicio['series']>['salud_suelo'][number];

export function GraficaSuelo({ datos }: { datos: Fila[] }) {
  const idTitulo = useId();
  const idResumen = useId();
  if (datos.length === 0) return null;

  const valores = datos.map((d) => d.valor);
  const minimo = Math.max(0, Math.min(...valores) - 5);
  const maximo = Math.min(100, Math.max(...valores) + 5);
  const linea = puntosLinea(valores, ANCHO, ALTO, minimo, maximo);
  const primero = datos[0];
  const ultimo = datos[datos.length - 1];
  const cambio = ultimo.valor - primero.valor;
  const texto =
    `Entre ${formatearMesAnio(primero.mes)} y ${formatearMesAnio(ultimo.mes)}, la salud de tu suelo ` +
    (cambio === 0
      ? `se mantuvo en ${formatearEntero(ultimo.valor)} de 100.`
      : `pasó de ${formatearEntero(primero.valor)} a ${formatearEntero(ultimo.valor)} de 100.`);

  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-3 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 id={idTitulo} className="font-titulo text-lg font-extrabold text-tinta">
            Salud de tu suelo
          </h2>
          <p className="text-sm text-tinta/75">Últimos {datos.length} meses, de 0 a 100</p>
        </div>
        {cambio !== 0 && (
          <span className={`rounded-full px-3 py-1 text-sm font-bold ${cambio > 0 ? 'bg-hoja/25 text-campo' : 'bg-[#D94F4F]/15 text-[#A33333]'}`}>
            {cambio > 0 ? '+' : '−'}
            {formatearEntero(Math.abs(cambio))} puntos
          </span>
        )}
      </div>

      <div className="rounded-2xl bg-crema p-3">
        <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} preserveAspectRatio="none" className="h-28 w-full" role="img" aria-labelledby={`${idTitulo} ${idResumen}`}>
          <title>Salud del suelo por mes</title>
          <polygon points={`0,${ALTO} ${linea} ${ANCHO},${ALTO}`} className="fill-hoja/25" />
          <polyline points={linea} fill="none" className="stroke-campo" strokeWidth={3} vectorEffect="non-scaling-stroke" />
        </svg>
        <div className="mt-2 flex justify-between text-sm font-semibold text-tinta/75" aria-hidden="true">
          <span>
            {formatearMesCorto(primero.mes)}: {formatearEntero(primero.valor)}
          </span>
          <span className="text-campo">
            {formatearMesCorto(ultimo.mes)}: {formatearEntero(ultimo.valor)}
          </span>
        </div>
      </div>
      <p id={idResumen} className="text-base text-tinta">{texto}</p>
    </section>
  );
}
