import type { ReactNode } from 'react';

export function TarjetaBeneficio({ icono, titulo, texto }: { icono: ReactNode; titulo: string; texto: string }) {
  return (
    <li className="flex min-w-0 flex-1 flex-col items-center gap-1 rounded-2xl bg-[#EAF1FB] px-2 py-3 text-center">
      <span className="text-campo">{icono}</span>
      <span className="font-titulo text-base font-extrabold leading-tight text-tinta">{titulo}</span>
      <span className="whitespace-nowrap text-sm leading-tight text-tinta/75">{texto}</span>
    </li>
  );
}
