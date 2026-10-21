// El avatar del Asistente SURCO: un brote. Nunca la foto de una persona.
import { IconoBrote } from '../iconos/Iconos';

export function AvatarAsistente({ tamano = 'normal' }: { tamano?: 'normal' | 'grande' }) {
  const caja = tamano === 'grande' ? 'h-14 w-14' : 'h-10 w-10';
  return (
    <span aria-hidden="true" className={`flex ${caja} shrink-0 items-center justify-center rounded-full bg-hoja/25 text-campo`}>
      <IconoBrote tamano={tamano === 'grande' ? 30 : 22} />
    </span>
  );
}
