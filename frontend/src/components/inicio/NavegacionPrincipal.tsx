// Navegación principal: UN solo <nav>. En celular es la barra inferior; desde 1024 px, la barra lateral.
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ComponentType } from 'react';
import { IconoAsistente, IconoCalendario, IconoCasa, IconoLotes, IconoPerfil } from '../iconos/Iconos';

interface Item {
  href: string;
  texto: string;
  Icono: ComponentType<{ tamano?: number; className?: string }>;
}

const ITEMS: Item[] = [
  { href: '/inicio', texto: 'Inicio', Icono: IconoCasa },
  { href: '/mis-lotes', texto: 'Mis lotes', Icono: IconoLotes },
  { href: '/plan-de-siembra', texto: 'Plan de siembra', Icono: IconoCalendario },
  { href: '/asistente', texto: 'Asistente', Icono: IconoAsistente },
  { href: '/perfil', texto: 'Perfil', Icono: IconoPerfil }
];

export function NavegacionPrincipal() {
  const ruta = usePathname();

  return (
    <nav
      aria-label="Navegación principal"
      className="fixed inset-x-0 bottom-0 z-[1200] border-t border-borde bg-white pb-[env(safe-area-inset-bottom)] lg:inset-y-0 lg:right-auto lg:w-64 lg:border-r lg:border-t-0 lg:px-3 lg:pb-0 lg:pt-24"
    >
      <ul className="grid grid-cols-5 lg:flex lg:flex-col lg:gap-1">
        {ITEMS.map(({ href, texto, Icono }) => {
          const activo = ruta === href || ruta.startsWith(`${href}/`);
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={activo ? 'page' : undefined}
                className={`flex min-h-16 flex-col items-center justify-center gap-1 px-1 text-center text-sm font-semibold leading-tight transition-colors lg:min-h-14 lg:flex-row lg:justify-start lg:gap-3 lg:rounded-2xl lg:px-4 lg:text-base ${
                  activo ? 'text-campo lg:bg-campo lg:text-white' : 'text-tinta/70 hover:text-campo lg:hover:bg-campo/10'
                }`}
              >
                <span className={`flex h-8 w-14 items-center justify-center rounded-full lg:h-auto lg:w-auto ${activo ? 'bg-hoja/25 lg:bg-transparent' : ''}`}>
                  <Icono tamano={24} />
                </span>
                {texto}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
