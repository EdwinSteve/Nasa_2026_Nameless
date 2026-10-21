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
export const IconoCampana = (p: P) => (
  <Icono {...p}><path d="M6 9a6 6 0 0112 0c0 5 2 6.5 2 6.5H4S6 14 6 9z" /><path d="M10 19a2 2 0 004 0" /></Icono>
);
export const IconoCasa = (p: P) => (
  <Icono {...p}><path d="M3 11l9-7 9 7" /><path d="M5 10v10h5v-6h4v6h5V10" /></Icono>
);
export const IconoLotes = (p: P) => (
  <Icono {...p}><rect x="3" y="3" width="8" height="8" rx="2" /><rect x="13" y="3" width="8" height="8" rx="2" /><rect x="3" y="13" width="8" height="8" rx="2" /><rect x="13" y="13" width="8" height="8" rx="2" /></Icono>
);
export const IconoAsistente = (p: P) => (
  <Icono {...p}><path d="M4 5h16v11H9l-5 4V5z" /><path d="M8 10h8M8 13h5" /></Icono>
);
export const IconoPerfil = (p: P) => (
  <Icono {...p}><circle cx="12" cy="8" r="4" /><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" /></Icono>
);
export const IconoMicrofono = (p: P) => (
  <Icono {...p}><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0014 0M12 18v3" /></Icono>
);
export const IconoSol = (p: P) => (
  <Icono {...p}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></Icono>
);
export const IconoNube = (p: P) => (
  <Icono {...p}><path d="M7 18a4 4 0 01-.5-8 6 6 0 0111.5 1.5A3.5 3.5 0 0117.5 18H7z" /></Icono>
);
export const IconoLluvia = (p: P) => (
  <Icono {...p}><path d="M7 15a4 4 0 01-.5-8 6 6 0 0111.5 1.5A3.5 3.5 0 0117.5 15H7z" /><path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3" /></Icono>
);
export const IconoTermometro = (p: P) => (
  <Icono {...p}><path d="M10 14V5a2 2 0 014 0v9a4 4 0 11-4 0z" /></Icono>
);
export const IconoHoja = (p: P) => (
  <Icono {...p}><path d="M5 19C5 10 11 5 20 4c0 9-5 15-14 15z" /><path d="M5 19l7-7" /></Icono>
);
export const IconoCheck = (p: P) => (
  <Icono {...p}><circle cx="12" cy="12" r="9" /><path d="M8 12l3 3 5-6" /></Icono>
);
export const IconoAyuda = (p: P) => (
  <Icono {...p}><circle cx="12" cy="12" r="9" /><path d="M9.5 9.5a2.5 2.5 0 114 2c-1 .7-1.5 1.2-1.5 2.5M12 17h.01" /></Icono>
);
export const IconoAlerta = (p: P) => (
  <Icono {...p}><path d="M12 3l9 16H3l9-16z" /><path d="M12 10v4M12 17h.01" /></Icono>
);
export const IconoCosecha = (p: P) => (
  <Icono {...p}><path d="M12 21V9" /><path d="M12 9c-2-1-3-3-3-5 2 0 3 2 3 5zM12 9c2-1 3-3 3-5-2 0-3 2-3 5zM12 14c-2-1-3-3-3-5 2 0 3 2 3 5zM12 14c2-1 3-3 3-5-2 0-3 2-3 5z" /></Icono>
);
export const IconoFlecha = (p: P) => (
  <Icono {...p}><path d="M5 12h14M13 6l6 6-6 6" /></Icono>
);
export const IconoAtras = (p: P) => (
  <Icono {...p}><path d="M15 5l-7 7 7 7" /></Icono>
);
export const IconoChevron = (p: P) => (
  <Icono {...p}><path d="M6 9l6 6 6-6" /></Icono>
);
export const IconoInsignia = (p: P) => (
  <Icono {...p}><circle cx="12" cy="9" r="6" /><path d="M8.5 14L7 22l5-3 5 3-1.5-8" /></Icono>
);
