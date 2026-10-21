// Aviso cuando no se puede grabar: sin permiso, sin micrófono o navegador sin soporte. El texto sigue funcionando.
import type { EstadoGrabadora } from '../../hooks/useGrabadora';
import { IconoCerrar, IconoMicrofono } from '../iconos/Iconos';

interface Props {
  estado: EstadoGrabadora;
  onPermitir: () => void;
  onCerrar: () => void;
}

export function AvisoMicrofono({ estado, onPermitir, onCerrar }: Props) {
  if (estado !== 'sin_permiso' && estado !== 'sin_microfono' && estado !== 'no_soportado') return null;

  const texto =
    estado === 'sin_permiso'
      ? 'Si no le aparece la pregunta, actívelo en la configuración del navegador. Mientras tanto puede escribir.'
      : estado === 'sin_microfono'
        ? 'No encontramos un micrófono en este equipo. Puede escribir su pregunta.'
        : 'Este navegador no permite grabar notas de voz. Puede escribir su pregunta.';

  return (
    <div role="alert" className="flex items-start gap-3 rounded-2xl border-2 border-sol/50 bg-sol/10 p-3">
      <IconoMicrofono tamano={22} className="mt-1 shrink-0 text-[#B5601F]" />
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <p className="text-base font-bold text-tinta">{estado === 'sin_permiso' ? 'Para hablar, permita el micrófono' : 'No podemos grabar su voz'}</p>
        <p className="text-sm text-tinta/80">{texto}</p>
        {estado === 'sin_permiso' && (
          <button type="button" onClick={onPermitir} className="min-h-14 self-start rounded-full bg-campo px-6 text-base font-bold text-white hover:bg-[#16381F]">
            Permitir
          </button>
        )}
      </div>
      <button type="button" onClick={onCerrar} aria-label="Cerrar aviso" className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full text-tinta/70 hover:bg-tinta/5">
        <IconoCerrar tamano={22} />
      </button>
    </div>
  );
}
