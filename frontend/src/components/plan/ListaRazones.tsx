// "¿Por qué se lo recomendamos?": cada razón con el chip de la fuente del dato.
import { useId } from 'react';
import type { Razon } from '../../api/tipos';
import { IconoCheck } from '../iconos/Iconos';
import { ChipFuente } from '../inicio/ChipFuente';

export function ListaRazones({ razones, titulo = '¿Por qué se lo recomendamos?' }: { razones: Razon[]; titulo?: string }) {
  const idTitulo = useId();
  if (razones.length === 0) return null;

  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-4 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <h2 id={idTitulo} className="font-titulo text-xl font-extrabold text-tinta">
        {titulo}
      </h2>
      <ul className="flex flex-col gap-3">
        {razones.map((r, i) => (
          <li key={i} className="flex items-start gap-3 rounded-2xl bg-crema p-4">
            <IconoCheck tamano={22} className="mt-0.5 shrink-0 text-campo" />
            <div className="flex flex-col items-start gap-2">
              <p className="text-base leading-relaxed text-tinta">{r.texto}</p>
              <ChipFuente procedencia={r.procedencia} />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
