// "Qué tanto le conviene cada cultivo a su lote": barra de 0 a 1; los no aptos al final y en gris.
import Link from 'next/link';
import { useId } from 'react';
import type { CultivoRanking } from '../../api/tipos';
import { formatearIp, ordenarRanking } from '../../lib/plan';
import { IconoAlerta, IconoFlecha } from '../iconos/Iconos';

interface Props {
  ranking: CultivoRanking[];
  hrefCultivo: (cultivoId: string) => string;
}

export function ListaRanking({ ranking, hrefCultivo }: Props) {
  const idTitulo = useId();
  const ordenado = ordenarRanking(ranking);

  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-4 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <div>
        <h2 id={idTitulo} className="font-titulo text-xl font-extrabold text-tinta">
          Qué tanto le conviene cada cultivo a su lote
        </h2>
        <p className="text-sm text-tinta/75">De 0 a 1: entre más larga la barra, mejor le va en su lote.</p>
      </div>

      <ol className="flex flex-col gap-2">
        {ordenado.map((c) => {
          const valor = formatearIp(c.ip);
          const barra = (
            <span aria-hidden="true" className="block h-3 w-full overflow-hidden rounded-full bg-[#EDE7DA]">
              <span
                className={`block h-full rounded-full ${c.apto ? 'bg-campo' : 'bg-tinta/30'}`}
                style={{ width: `${Math.round(Math.max(0, Math.min(1, c.ip)) * 100)}%` }}
              />
            </span>
          );

          if (!c.apto) {
            return (
              <li key={c.cultivo_id} className="flex flex-col gap-1.5 rounded-2xl bg-crema/70 p-3">
                <span className="flex items-center justify-between gap-2">
                  <span className="text-base font-bold text-tinta/70">{c.nombre}</span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#F3E3E3] px-2.5 py-0.5 text-sm font-bold text-[#8A2E2E]">
                    <IconoAlerta tamano={16} />
                    No recomendado aquí
                  </span>
                </span>
                {barra}
                {c.razon_no_apto && <span className="text-sm text-tinta/80">{c.razon_no_apto}</span>}
              </li>
            );
          }

          return (
            <li key={c.cultivo_id}>
              <Link
                href={hrefCultivo(c.cultivo_id)}
                className="flex flex-col gap-1.5 rounded-2xl p-3 hover:bg-campo/5"
                aria-label={`${c.nombre}: ${valor} de 1. Ver cuándo sembrar`}
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="text-base font-bold text-tinta">{c.nombre}</span>
                  <span className="flex items-center gap-1 text-base font-bold text-campo">
                    {valor}
                    <IconoFlecha tamano={18} className="text-tinta/40" />
                  </span>
                </span>
                {barra}
              </Link>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
