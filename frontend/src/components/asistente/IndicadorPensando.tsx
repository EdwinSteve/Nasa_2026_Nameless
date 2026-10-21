// "El asistente está escribiendo": tres puntos. Con "reducir movimiento" quedan quietos.
import { AvatarAsistente } from './AvatarAsistente';

export function IndicadorPensando() {
  return (
    <div className="flex items-end gap-2">
      <AvatarAsistente />
      <div className="flex min-h-12 items-center gap-1.5 rounded-3xl rounded-bl-md bg-white px-5 shadow-sm">
        <span className="sr-only">El asistente está preparando su respuesta…</span>
        {[0, 150, 300].map((retraso) => (
          <span
            key={retraso}
            aria-hidden="true"
            className="h-2.5 w-2.5 animate-bounce rounded-full bg-campo/60 motion-reduce:animate-none"
            style={{ animationDelay: `${retraso}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
