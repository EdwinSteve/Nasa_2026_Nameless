// Agua usada (barras) y recomendada (línea punteada) por mes, en SVG propio.
import { useId } from 'react';
import type { ResumenInicio } from '../../api/tipos';
import { formatearEntero, formatearMesAnio, formatearMesCorto } from '../../lib/fechas';
import { techoEje, xCentros, yDe } from '../../lib/graficas';

const ANCHO = 300;
const ALTO = 140;

type Fila = NonNullable<ResumenInicio['series']>['agua_mensual'][number];

function resumen(datos: Fila[]): string {
  const ultimo = datos[datos.length - 1];
  const diferencia = ultimo.recomendada_m3_ha - ultimo.usada_m3_ha;
  const mes = formatearMesAnio(ultimo.mes);
  if (diferencia > 0) {
    const pct = Math.round((diferencia / ultimo.recomendada_m3_ha) * 100);
    return `En ${mes} usaste ${formatearEntero(ultimo.usada_m3_ha)} m³ por hectárea, ${pct} % menos de lo recomendado.`;
  }
  if (diferencia < 0) {
    return `En ${mes} usaste ${formatearEntero(ultimo.usada_m3_ha)} m³ por hectárea, ${formatearEntero(-diferencia)} m³ más de lo recomendado.`;
  }
  return `En ${mes} usaste justo lo recomendado: ${formatearEntero(ultimo.usada_m3_ha)} m³ por hectárea.`;
}

export function GraficaAgua({ datos }: { datos: Fila[] }) {
  const idTitulo = useId();
  const idResumen = useId();
  if (datos.length === 0) return null;

  const techo = techoEje(datos.flatMap((d) => [d.usada_m3_ha, d.recomendada_m3_ha]));
  const xs = xCentros(datos.length, ANCHO);
  const anchoBarra = (ANCHO / datos.length) * 0.55;
  const linea = datos.map((d, i) => `${xs[i].toFixed(1)},${yDe(d.recomendada_m3_ha, techo, ALTO).toFixed(1)}`).join(' ');
  const texto = resumen(datos);

  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-3 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <div>
        <h2 id={idTitulo} className="font-titulo text-lg font-extrabold text-tinta">
          Agua usada y recomendada
        </h2>
        <p className="text-sm text-tinta/75">Metros cúbicos por hectárea, últimos {datos.length} meses</p>
      </div>

      <div className="rounded-2xl bg-crema p-3">
        <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} preserveAspectRatio="none" className="h-40 w-full" role="img" aria-labelledby={`${idTitulo} ${idResumen}`}>
          <title>Agua usada y recomendada por mes</title>
          {datos.map((d, i) => {
            const y = yDe(d.usada_m3_ha, techo, ALTO);
            const ultimo = i === datos.length - 1;
            return (
              <rect
                key={d.mes}
                x={xs[i] - anchoBarra / 2}
                y={y}
                width={anchoBarra}
                height={ALTO - y}
                rx={3}
                className={ultimo ? 'fill-campo' : 'fill-agua/40'}
              />
            );
          })}
          <polyline points={linea} fill="none" className="stroke-[#B5601F]" strokeWidth={2.5} strokeDasharray="6 4" vectorEffect="non-scaling-stroke" />
        </svg>
        <div className="mt-2 grid text-center text-sm font-semibold text-tinta/75" style={{ gridTemplateColumns: `repeat(${datos.length}, minmax(0, 1fr))` }} aria-hidden="true">
          {datos.map((d) => (
            <span key={d.mes}>{formatearMesCorto(d.mes)}</span>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-4 text-sm text-tinta/80" aria-hidden="true">
        <span className="flex items-center gap-1.5">
          <span className="h-3.5 w-3.5 rounded bg-agua/40" /> Agua usada
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-0 w-5 border-t-2 border-dashed border-[#B5601F]" /> Recomendada
        </span>
      </div>
      <p id={idResumen} className="text-base text-tinta">{texto}</p>
      <ul className="sr-only">
        {datos.map((d) => (
          <li key={d.mes}>
            {formatearMesAnio(d.mes)}: usaste {formatearEntero(d.usada_m3_ha)} m³ por hectárea; se recomendaban{' '}
            {formatearEntero(d.recomendada_m3_ha)}.
          </li>
        ))}
      </ul>
    </section>
  );
}
