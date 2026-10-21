// Marco común de las pantallas del plan: franja sin conexión, contenido, menú principal y micrófono.
import type { ReactNode } from 'react';
import { FranjaSinConexion } from '../feedback/FranjaSinConexion';
import { BotonMicrofono } from '../inicio/BotonMicrofono';
import { NavegacionPrincipal } from '../inicio/NavegacionPrincipal';

interface Props {
  children: ReactNode;
  sinConexion: boolean;
  textoSinConexion?: string;
}

export function MarcoPlan({ children, sinConexion, textoSinConexion }: Props) {
  return (
    <div className="min-h-dvh bg-crema text-tinta lg:pl-64">
      {sinConexion && <FranjaSinConexion texto={textoSinConexion} />}
      <div className="mx-auto flex max-w-[1280px] flex-col gap-5 px-4 pt-5 pb-36 lg:px-8 lg:pb-12">{children}</div>
      <NavegacionPrincipal />
      <BotonMicrofono />
    </div>
  );
}
