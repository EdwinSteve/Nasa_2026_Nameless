'use client';

// Pantalla de bienvenida: un solo carrusel que se reorganiza en dos columnas desde 1024 px.
import { useState, type KeyboardEvent } from 'react';
import { DIAPOSITIVAS } from '../components/bienvenida/diapositivas';
import { ImagenBienvenida } from '../components/bienvenida/ImagenBienvenida';
import { IndicadorCarrusel } from '../components/bienvenida/IndicadorCarrusel';
import { TarjetaBeneficio } from '../components/bienvenida/TarjetaBeneficio';
import { IconoBrote, IconoCalendario, IconoGota, IconoVerificacion } from '../components/iconos/Iconos';
import { useAltitud } from '../hooks/useAltitud';

export interface BienvenidaProps {
  onCrearCuenta: () => void;
  onIngresar: () => void;
}

export function Bienvenida({ onCrearCuenta, onIngresar }: BienvenidaProps) {
  const [actual, setActual] = useState(0);
  const altitud = useAltitud();
  const total = DIAPOSITIVAS.length;
  const diapositiva = DIAPOSITIVAS[actual];

  const ir = (indice: number) => setActual(Math.min(total - 1, Math.max(0, indice)));

  function alTeclado(e: KeyboardEvent<HTMLElement>) {
    if (e.key === 'ArrowRight') ir(actual + 1);
    if (e.key === 'ArrowLeft') ir(actual - 1);
  }

  return (
    <div className="min-h-dvh bg-[#F5F7FB] pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto grid w-full max-w-[430px] gap-4 px-4 pt-4 pb-6 lg:min-h-dvh lg:max-w-7xl lg:grid-cols-[55fr_45fr] lg:items-center lg:gap-14 lg:px-12">
        <section
          aria-roledescription="carrusel"
          aria-label="Qué hace SURCO"
          tabIndex={0}
          onKeyDown={alTeclado}
          className="rounded-3xl"
        >
          <ImagenBienvenida
            actual={actual}
            municipioTexto={altitud.municipioTexto}
            estadoAltitud={altitud.estado}
            altitudTexto={altitud.altitudTexto}
            onSolicitarAltitud={altitud.solicitarAltitud}
            onSiguiente={() => ir(actual + 1)}
            onAnterior={() => ir(actual - 1)}
          />
        </section>

        <div className="flex flex-col items-center text-center lg:items-start lg:text-left">
          <IndicadorCarrusel total={total} activo={actual} onSeleccionar={ir} />

          <div aria-live="polite" aria-roledescription="diapositiva" aria-label={`Diapositiva ${actual + 1} de ${total}`} className="mt-3">
            <h1 className="mx-auto max-w-[340px] font-titulo text-[28px] font-black leading-tight text-tinta lg:mx-0 lg:max-w-none lg:text-[40px]">
              {diapositiva.titulo}
            </h1>
            <p className="mx-auto mt-2 max-w-[340px] text-lg leading-relaxed text-tinta/80 lg:mx-0 lg:max-w-[460px]">
              {diapositiva.subtitulo}
            </p>
          </div>

          <ul className="mt-6 flex w-full gap-2" aria-label="Lo que le ayuda a decidir">
            <TarjetaBeneficio icono={<IconoGota />} titulo="Riego" texto="Cuánta agua" />
            <TarjetaBeneficio icono={<IconoCalendario />} titulo="Siembra" texto="Mejor fecha" />
            <TarjetaBeneficio icono={<IconoBrote />} titulo="Rotación" texto="Suelo sano" />
          </ul>

          <div className="mt-6 flex w-full flex-col gap-3 lg:flex-row">
            <button
              type="button"
              onClick={onCrearCuenta}
              className="min-h-14 w-full rounded-2xl bg-campo px-6 font-titulo text-lg font-extrabold text-white shadow-md hover:bg-[#16381F] lg:flex-1"
            >
              Crear mi cuenta
            </button>
            <button
              type="button"
              onClick={onIngresar}
              className="min-h-14 w-full rounded-2xl px-6 font-titulo text-[17px] font-extrabold text-campo hover:bg-campo/5 lg:w-auto"
            >
              Ya tengo cuenta
            </button>
          </div>

          <p className="mt-5 inline-flex items-center gap-2 rounded-full bg-[#EAF1FB] px-4 py-2 text-sm font-semibold text-tinta/90">
            <IconoVerificacion tamano={18} className="shrink-0 text-campo" />
            Tecnología satelital para el campo colombiano
          </p>
        </div>
      </div>
    </div>
  );
}
