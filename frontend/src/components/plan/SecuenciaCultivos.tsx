// Los cultivos de una rotación, en orden, con flechas entre ellos.
import { Fragment } from 'react';
import type { Rotacion } from '../../api/tipos';
import { IconoFlecha } from '../iconos/Iconos';

export function SecuenciaCultivos({ secuencia, grande = false }: { secuencia: Rotacion['secuencia']; grande?: boolean }) {
  return (
    <ol
      aria-label={`Rotación: ${secuencia.map((c) => c.nombre).join(', luego ')}`}
      className={`flex flex-wrap items-center ${grande ? 'gap-2' : 'gap-1.5'}`}
    >
      {secuencia.map((c, i) => (
        <Fragment key={`${c.cultivo_id}-${i}`}>
          {i > 0 && (
            <li aria-hidden="true" className="text-tinta/50">
              <IconoFlecha tamano={grande ? 22 : 18} />
            </li>
          )}
          <li
            className={
              grande
                ? 'rounded-2xl bg-hoja/20 px-4 py-2 font-titulo text-lg font-extrabold text-campo'
                : 'text-base font-bold text-tinta'
            }
          >
            {c.nombre}
          </li>
        </Fragment>
      ))}
    </ol>
  );
}
