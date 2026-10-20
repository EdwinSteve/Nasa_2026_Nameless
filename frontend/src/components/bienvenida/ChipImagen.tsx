import type { ReactNode } from 'react';

export function ChipImagen({ icono, texto, puntoVerde = false }: { icono?: ReactNode; texto: string; puntoVerde?: boolean }) {
  return (
    <span className="inline-flex h-9 max-w-[60%] items-center gap-1.5 rounded-full bg-white/92 px-3.5 text-tinta shadow-sm">
      {puntoVerde && <span className="h-2 w-2 shrink-0 rounded-full bg-hoja" aria-hidden="true" />}
      {icono && <span className="shrink-0 text-campo">{icono}</span>}
      <span className="truncate text-sm font-semibold leading-none">{texto}</span>
    </span>
  );
}
