// Botón flotante para hablarle al asistente. En celular queda encima de la barra inferior, sin taparla.
import Link from 'next/link';
import { IconoMicrofono } from '../iconos/Iconos';

export function BotonMicrofono() {
  return (
    <Link
      href="/asistente"
      aria-label="Hablar con el asistente"
      className="fixed right-4 bottom-[calc(5.5rem+env(safe-area-inset-bottom))] z-[1250] flex h-16 w-16 items-center justify-center rounded-full bg-campo text-white shadow-lg transition-transform hover:bg-[#16381F] active:scale-95 lg:right-8 lg:bottom-8"
    >
      <IconoMicrofono tamano={28} />
    </Link>
  );
}
