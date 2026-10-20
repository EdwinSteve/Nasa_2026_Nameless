// Íconos SVG de 24 px, trazo de 2 px y currentColor.
import type { ReactNode } from 'react';

function Icono({ children, tamano = 24, className = '' }: { children: ReactNode; tamano?: number; className?: string }) {
  return (
    <svg width={tamano} height={tamano} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {children}
    </svg>
  );
}

type P = { tamano?: number; className?: string };

export const IconoSatelite = (p: P) => (
  <Icono {...p}><rect x="9" y="9" width="6" height="6" rx="1" transform="rotate(45 12 12)" /><path d="M4 4l4 4M16 16l4 4M2.5 9.5l7-7M14.5 21.5l7-7M18 3a3 3 0 013 3" /></Icono>
);
export const IconoUbicacion = (p: P) => (
  <Icono {...p}><path d="M12 21c-4-4.5-7-8.5-7-12a7 7 0 1114 0c0 3.5-3 7.5-7 12z" /><circle cx="12" cy="9" r="2.5" /></Icono>
);
export const IconoMontana = (p: P) => (
  <Icono {...p}><path d="M3 20l6-11 4 6 2-3 6 8z" /></Icono>
);
export const IconoGota = (p: P) => (
  <Icono {...p}><path d="M12 3C9 7.5 6 10.5 6 14a6 6 0 0012 0c0-3.5-3-6.5-6-11z" /></Icono>
);
export const IconoCalendario = (p: P) => (
  <Icono {...p}><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M8 3v4M16 3v4M3 10h18" /></Icono>
);
export const IconoBrote = (p: P) => (
  <Icono {...p}><path d="M12 21v-9M12 12C12 7 8 5 4 5c0 4 2.5 7 8 7zM12 12c0-5 4-7 8-7 0 4-2.5 7-8 7z" /></Icono>
);
export const IconoVerificacion = (p: P) => (
  <Icono {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" /></Icono>
);
