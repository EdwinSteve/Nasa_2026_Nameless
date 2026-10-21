// El lote principal: mapa satelital de solo lectura, etapas del cultivo e indicadores.
'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useId, useMemo } from 'react';
import type { ResumenInicio } from '../../api/tipos';
import { calcularCentroide, poligonoAEsquinas } from '../../lib/geo';
import { formatearEntero, formatearUnDecimal } from '../../lib/fechas';
import { IconoUbicacion } from '../iconos/Iconos';
import { EtapasCultivo } from './EtapasCultivo';
import { IndicadoresLote } from './IndicadoresLote';

// El mismo mapa del registro (Leaflet), sin modo de edición. Necesita el navegador.
const MapaPuntos = dynamic(() => import('../forms/MapaPuntos'), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-[#1D3323] motion-reduce:animate-none" />
});

const sinAccion = () => undefined;

type Lote = NonNullable<ResumenInicio['lote_principal']>;

export function TarjetaLote({ lote }: { lote: Lote }) {
  const idTitulo = useId();
  const esquinas = useMemo(() => poligonoAEsquinas(lote.poligono), [lote.poligono]);
  const centroide = useMemo(() => calcularCentroide(lote.poligono), [lote.poligono]);
  const detalle = [
    `${formatearUnDecimal(lote.area_ha)} ha`,
    lote.corregimiento_nombre,
    lote.altitud_msnm != null ? `${formatearEntero(lote.altitud_msnm)} m de altitud` : null
  ].filter(Boolean);

  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-5 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <div>
        <h2 id={idTitulo} className="font-titulo text-2xl font-extrabold text-tinta">
          Mi lote · {lote.nombre}
        </h2>
        <p className="flex items-start gap-1 text-base text-tinta/75">
          <IconoUbicacion tamano={18} className="mt-0.5 shrink-0 text-sol" />
          <span className="min-w-0">{detalle.join(' · ')}</span>
        </p>
      </div>

      <div className="relative isolate h-56 overflow-hidden rounded-2xl border-2 border-campo sm:h-72 lg:h-96">
        <MapaPuntos
          esquinas={esquinas}
          cerrado
          centroide={centroide}
          centro={null}
          interactivo={false}
          onAgregar={sinAccion}
          onMover={sinAccion}
        />
      </div>

      {lote.cultivo ? (
        <EtapasCultivo cultivo={lote.cultivo} />
      ) : (
        <div className="flex flex-col gap-2 rounded-2xl bg-crema p-4">
          <p className="text-base font-semibold text-tinta">Todavía no tiene un cultivo registrado en este lote.</p>
          <Link href={`/lotes/${encodeURIComponent(lote.id)}`} className="text-base font-bold text-campo underline">
            Ver qué me conviene sembrar
          </Link>
        </div>
      )}

      <IndicadoresLote indicadores={lote.indicadores} />
    </section>
  );
}

/** Usuario sin lotes: lo primero es marcar uno. */
export function TarjetaMarcarLote() {
  const idTitulo = useId();
  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-3 rounded-3xl border-2 border-dashed border-campo/40 bg-white p-6">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-hoja/25 text-campo">
        <IconoUbicacion tamano={26} />
      </span>
      <h2 id={idTitulo} className="font-titulo text-2xl font-extrabold text-tinta">
        Marque su primer lote
      </h2>
      <p className="text-base text-tinta/80">
        Dibuje el borde de su terreno en el mapa y lo leeremos con los satélites: humedad de la tierra, verdor y clima.
      </p>
      <Link
        href="/mis-lotes"
        className="flex min-h-14 items-center justify-center rounded-full bg-campo px-6 text-base font-bold text-white hover:bg-[#16381F] sm:self-start"
      >
        Marcar mi lote
      </Link>
    </section>
  );
}
