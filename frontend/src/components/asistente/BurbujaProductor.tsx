// Mensaje del productor: texto o nota de voz (onda, duración y la transcripción debajo).
import type { MensajeVista } from '../../hooks/useConversacion';
import { duracionEnPalabras, formatearDuracion, horaMensaje, ondaDecorativa } from '../../lib/asistente';
import { IconoAlerta, IconoMicrofono } from '../iconos/Iconos';
import { OndaVoz } from './OndaVoz';

interface Props {
  mensaje: MensajeVista;
  onReintentar: (id: string) => void;
  /** Sin conexión o mientras el asistente responde no se puede reintentar. */
  puedeReintentar: boolean;
}

export function BurbujaProductor({ mensaje, onReintentar, puedeReintentar }: Props) {
  const esVoz = mensaje.audio_duracion_s !== null;
  const fallido = mensaje.envio === 'fallido';

  return (
    <div className="flex flex-col items-end gap-1">
      <div
        className={`flex max-w-[85%] flex-col gap-2 rounded-3xl rounded-br-md px-4 py-3 shadow-sm lg:max-w-[70%] ${
          fallido ? 'border-2 border-[#D94F4F] bg-[#FFF5F5] text-tinta' : 'bg-campo text-white'
        }`}
      >
        {esVoz && mensaje.audio_duracion_s !== null && (
          <div className="flex min-w-48 items-center gap-3">
            <IconoMicrofono tamano={20} className="shrink-0" />
            <OndaVoz niveles={ondaDecorativa(mensaje.id)} clase={fallido ? 'bg-campo/50' : 'bg-white/80'} />
            <span className="shrink-0 text-sm font-bold tabular-nums">
              <span aria-hidden="true">{formatearDuracion(mensaje.audio_duracion_s)}</span>
              <span className="sr-only">Nota de voz de {duracionEnPalabras(mensaje.audio_duracion_s)}</span>
            </span>
          </div>
        )}
        {mensaje.texto ? (
          <p className={`text-base leading-relaxed ${esVoz ? (fallido ? 'border-t border-tinta/15 pt-2' : 'border-t border-white/25 pt-2') : ''}`}>
            {esVoz && <span className="sr-only">Transcripción: </span>}
            {mensaje.texto}
          </p>
        ) : (
          mensaje.envio === 'transcribiendo' && <p className="text-base italic opacity-90">Pasando su voz a texto…</p>
        )}
      </div>

      <p className="flex min-h-6 items-center gap-1 text-sm text-tinta/70">
        {mensaje.envio === 'enviando' || mensaje.envio === 'transcribiendo' ? (
          'Enviando…'
        ) : fallido ? (
          <span role="alert" className="flex flex-wrap items-center justify-end gap-x-2 font-semibold text-[#A33333]">
            <IconoAlerta tamano={16} />
            No se envió ·
            <button
              type="button"
              onClick={() => onReintentar(mensaje.id)}
              disabled={!puedeReintentar}
              className="min-h-14 px-2 font-bold text-campo underline disabled:opacity-50"
            >
              Reintentar
            </button>
          </span>
        ) : (
          <>
            <span className="sr-only">Usted, </span>
            {horaMensaje(mensaje.creado_en)}
          </>
        )}
      </p>
    </div>
  );
}
