// Tarjetas de la pantalla Plan cuando todavía no hay plan que mostrar, y su esqueleto de carga.
import Link from 'next/link';
import type { ReactNode } from 'react';
import { IconoCalendario, IconoSatelite, IconoUbicacion } from '../iconos/Iconos';
import { Esqueleto } from '../inicio/Esqueleto';

interface TarjetaProps {
  icono: ReactNode;
  titulo: string;
  texto: string;
  accion: ReactNode;
  error?: string | null;
}

function TarjetaEstado({ icono, titulo, texto, accion, error }: TarjetaProps) {
  return (
    <section className="flex flex-col items-start gap-4 rounded-3xl border-2 border-dashed border-campo/30 bg-white p-6 lg:max-w-2xl">
      <span className="flex h-14 w-14 items-center justify-center rounded-full bg-hoja/20 text-campo">{icono}</span>
      <div>
        <h2 className="font-titulo text-2xl font-extrabold text-tinta">{titulo}</h2>
        <p className="mt-1 text-base leading-relaxed text-tinta/80">{texto}</p>
      </div>
      {accion}
      {error && (
        <p role="alert" className="text-base font-semibold text-[#B23B3B]">
          {error}
        </p>
      )}
    </section>
  );
}

const claseBoton =
  'flex min-h-14 w-full items-center justify-center rounded-full bg-campo px-6 text-base font-bold text-white shadow-sm hover:bg-[#16381F] disabled:opacity-70 sm:w-auto';

interface AccionProps {
  onAccion: () => void;
  ocupado: boolean;
  error: string | null;
}

export function SinDiagnostico({ onAccion, ocupado, error }: AccionProps) {
  return (
    <TarjetaEstado
      icono={<IconoSatelite tamano={28} />}
      titulo="Primero necesitamos analizar su lote"
      texto="Leemos su lote con satélites de la NASA: la humedad de la tierra, el verdor y el clima. Con eso armamos su plan de siembra."
      accion={
        <button type="button" onClick={onAccion} disabled={ocupado} className={claseBoton}>
          {ocupado ? 'Empezando…' : 'Analizar mi lote'}
        </button>
      }
      error={error}
    />
  );
}

export function SinPlan({ onAccion, ocupado, error }: AccionProps) {
  return (
    <TarjetaEstado
      icono={<IconoCalendario tamano={28} />}
      titulo="Este lote todavía no tiene plan de siembra"
      texto="Comparamos 40 años de clima de su zona y el pronóstico de El Niño y La Niña para decirle qué sembrar y en qué orden."
      accion={
        <button type="button" onClick={onAccion} disabled={ocupado} className={claseBoton}>
          {ocupado ? 'Empezando…' : 'Armar mi plan de siembra'}
        </button>
      }
      error={error}
    />
  );
}

export function SinLotes() {
  return (
    <TarjetaEstado
      icono={<IconoUbicacion tamano={28} />}
      titulo="Marque su primer lote"
      texto="Para armar su plan de siembra necesitamos saber dónde está su lote."
      accion={
        <Link href="/mis-lotes" className={claseBoton}>
          Marcar mi lote
        </Link>
      }
    />
  );
}

/** La forma de la pantalla Plan mientras carga: rotaciones a la izquierda y ranking a la derecha. */
export function EsqueletoPlan() {
  return (
    <div role="status" className="flex flex-col gap-5 lg:grid lg:grid-cols-12">
      <span className="sr-only">Cargando su plan de siembra…</span>
      <div className="flex flex-col gap-4 lg:col-span-7">
        <Esqueleto className="h-80" />
        <Esqueleto className="h-24" />
        <Esqueleto className="h-24" />
      </div>
      <div className="flex flex-col gap-4 lg:col-span-5">
        <Esqueleto className="h-96" />
      </div>
    </div>
  );
}
