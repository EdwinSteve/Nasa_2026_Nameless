// Respuesta del Asistente SURCO: texto corto, tarjetas de datos con su fuente, enlaces y valoración.
import Link from 'next/link';
import type { MensajeVista } from '../../hooks/useConversacion';
import { horaMensaje } from '../../lib/asistente';
import { IconoFlecha, IconoMeSirvio, IconoNoMeSirvio } from '../iconos/Iconos';
import { ChipFuente } from '../inicio/ChipFuente';
import { AvatarAsistente } from './AvatarAsistente';

interface Props {
  mensaje: MensajeVista;
  onValorar: (id: string, util: boolean) => void;
  desactivado: boolean;
}

export function BurbujaAsistente({ mensaje, onValorar, desactivado }: Props) {
  const botonValorar = (util: boolean) => {
    const elegido = mensaje.valoracion === util;
    return (
      <button
        type="button"
        onClick={() => onValorar(mensaje.id, util)}
        aria-pressed={elegido}
        disabled={desactivado}
        className={`flex min-h-14 items-center gap-2 rounded-full border-2 px-4 text-base font-semibold disabled:opacity-60 ${
          elegido ? 'border-campo bg-campo text-white' : 'border-borde bg-white text-tinta hover:border-campo/50'
        }`}
      >
        {util ? <IconoMeSirvio tamano={20} /> : <IconoNoMeSirvio tamano={20} />}
        {util ? 'Me sirvió' : 'No me sirvió'}
      </button>
    );
  };

  return (
    <div className="flex items-start gap-2">
      <AvatarAsistente />
      <div className="flex min-w-0 max-w-[92%] flex-col gap-2 lg:max-w-[80%]">
        <div className="flex flex-col gap-3 rounded-3xl rounded-tl-md bg-white p-4 shadow-sm">
          <p className="text-base leading-relaxed text-tinta">
            <span className="sr-only">Asistente SURCO: </span>
            {mensaje.texto}
          </p>

          {mensaje.tarjetas.length > 0 && (
            <ul className="grid gap-2 sm:grid-cols-2">
              {mensaje.tarjetas.map((t, i) => (
                <li key={i} className="flex flex-col items-start gap-1.5 rounded-2xl bg-crema p-3">
                  <span className="text-sm font-semibold text-tinta/75">{t.etiqueta}</span>
                  <span className="font-titulo text-xl font-extrabold text-tinta">
                    {t.valor}
                    {t.unidad && <span className="ml-1 text-base font-bold text-tinta/80">{t.unidad}</span>}
                  </span>
                  <ChipFuente procedencia={t.procedencia} />
                </li>
              ))}
            </ul>
          )}

          {mensaje.enlaces.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {mensaje.enlaces.map((e) => (
                <Link
                  key={e.ruta}
                  href={e.ruta}
                  className="flex min-h-14 items-center gap-2 rounded-full bg-hoja/20 px-5 text-base font-bold text-campo hover:bg-hoja/30"
                >
                  {e.texto}
                  <IconoFlecha tamano={18} />
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="¿Le sirvió esta respuesta?">
          {botonValorar(true)}
          {botonValorar(false)}
          <span className="text-sm text-tinta/70">{horaMensaje(mensaje.creado_en)}</span>
        </div>
        {mensaje.valoracion !== undefined && (
          <p role="status" className="text-sm text-tinta/75">
            Gracias por contarnos.
          </p>
        )}
      </div>
    </div>
  );
}
