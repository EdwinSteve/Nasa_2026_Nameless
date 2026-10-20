'use client';

// Tarjeta con la ilustración, los chips y el gesto de deslizar.
import Image from 'next/image';
import { useRef, useState, type PointerEvent } from 'react';
import { ALT_IMAGEN_BIENVENIDA, IMAGEN_BIENVENIDA } from './diapositivas';
import { ChipImagen } from './ChipImagen';
import { ChipAltitud } from './ChipAltitud';
import { IconoSatelite, IconoUbicacion } from '../iconos/Iconos';
import type { EstadoAltitud } from '../../hooks/useAltitud';

const UMBRAL_DESLIZAR_PX = 50;

export interface ImagenBienvenidaProps {
  encuadre: string;
  municipioTexto: string;
  estadoAltitud: EstadoAltitud;
  altitudTexto: string | null;
  onSolicitarAltitud: () => void;
  onSiguiente: () => void;
  onAnterior: () => void;
}

export function ImagenBienvenida(props: ImagenBienvenidaProps) {
  const inicioX = useRef<number | null>(null);
  const [imagenFallo, setImagenFallo] = useState(false);

  function alSoltar(e: PointerEvent<HTMLDivElement>) {
    if (inicioX.current === null) return;
    const distancia = e.clientX - inicioX.current;
    inicioX.current = null;
    if (distancia <= -UMBRAL_DESLIZAR_PX) props.onSiguiente();
    else if (distancia >= UMBRAL_DESLIZAR_PX) props.onAnterior();
  }

  return (
    <div
      className="relative h-[330px] w-full touch-pan-y overflow-hidden rounded-3xl bg-campo shadow-md lg:h-[560px]"
      onPointerDown={(e) => { inicioX.current = e.clientX; }}
      onPointerUp={alSoltar}
      onPointerCancel={() => { inicioX.current = null; }}
    >
      {!imagenFallo && (
        <Image
          src={IMAGEN_BIENVENIDA}
          alt={ALT_IMAGEN_BIENVENIDA}
          fill
          priority
          sizes="(min-width: 1024px) 55vw, 100vw"
          draggable={false}
          onError={() => setImagenFallo(true)}
          style={{ objectPosition: props.encuadre }}
          className="object-cover transition-[object-position] duration-500 ease-out motion-reduce:transition-none"
        />
      )}

      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-campo/70 to-transparent" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-campo/70 to-transparent" />

      <div className="absolute inset-x-3.5 top-3.5 flex items-center justify-between gap-2">
        <ChipImagen icono={<IconoSatelite tamano={18} />} texto="Datos de la NASA" />
        <ChipImagen icono={<IconoUbicacion tamano={18} />} texto={props.municipioTexto} />
      </div>
      <div className="absolute inset-x-3.5 bottom-3.5 flex items-center justify-between gap-2">
        <ChipImagen puntoVerde texto="Surcos mapeados" />
        <ChipAltitud estado={props.estadoAltitud} altitudTexto={props.altitudTexto} onSolicitar={props.onSolicitarAltitud} />
      </div>
    </div>
  );
}
