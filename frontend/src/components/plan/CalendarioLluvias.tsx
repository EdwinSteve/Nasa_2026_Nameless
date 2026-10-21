// "Lluvias esperadas": mes a mes, la lluvia en palabras con gotas o sol y una nota corta.
import { useId } from 'react';
import type { LluviaMensual } from '../../api/tipos';
import { formatearMesLargo } from '../../lib/fechas';
import { lluviaEnPalabras } from '../../lib/plan';
import { IconoGota, IconoSol } from '../iconos/Iconos';
import { ChipFuente } from '../inicio/ChipFuente';

export function CalendarioLluvias({ meses }: { meses: LluviaMensual[] }) {
  const idTitulo = useId();
  if (meses.length === 0) return null;

  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-4 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 id={idTitulo} className="font-titulo text-xl font-extrabold text-tinta">
            Lluvias esperadas
          </h2>
          <p className="text-sm text-tinta/75">Para planear la siembra, el abono y la cosecha.</p>
        </div>
        <ChipFuente procedencia={meses[0].procedencia} />
      </div>

      <ol className="flex flex-col gap-2">
        {meses.map((m, i) => {
          const { texto, gotas } = lluviaEnPalabras(m);
          return (
            <li
              key={m.mes}
              className={`grid grid-cols-[minmax(6.5rem,auto)_1fr] items-center gap-x-3 gap-y-1 rounded-2xl p-3 ${
                m.nivel === 'lluvioso' ? 'bg-hoja/15' : m.nivel === 'seco' ? 'bg-sol/10' : 'bg-crema'
              }`}
            >
              <span className="flex flex-col">
                <span className="text-base font-extrabold text-tinta">{formatearMesLargo(m.mes)}</span>
                {i === 0 && <span className="text-sm font-semibold text-tinta/70">Este mes</span>}
              </span>
              <span className="flex flex-col items-end gap-0.5 text-right">
                <span className="flex items-center gap-2 text-base font-bold text-tinta">
                  <span aria-hidden="true" className="flex">
                    {gotas === 0 ? (
                      <IconoSol tamano={22} className="text-sol" />
                    ) : (
                      Array.from({ length: gotas }, (_, g) => <IconoGota key={g} tamano={20} className="-mr-1 text-agua" />)
                    )}
                  </span>
                  {texto}
                </span>
                {m.nota && <span className="text-sm text-tinta/80">{m.nota}</span>}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
