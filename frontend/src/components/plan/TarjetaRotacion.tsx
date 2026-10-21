// Una de las mejores rotaciones del lote. Se abre y se cierra; la primera llega abierta.
'use client';

import Link from 'next/link';
import { useId } from 'react';
import type { Rotacion } from '../../api/tipos';
import { formatearEntero } from '../../lib/fechas';
import { textoFrecuencia } from '../../lib/plan';
import { IconoBrote, IconoChevron, IconoFlecha, IconoGota, IconoInsignia, IconoVerificacion } from '../iconos/Iconos';
import { SecuenciaCultivos } from './SecuenciaCultivos';

interface Props {
  rotacion: Rotacion;
  posicion: number;
  abierta: boolean;
  onAlternar: () => void;
  hrefDetalle: string;
}

export function TarjetaRotacion({ rotacion, posicion, abierta, onAlternar, hrefDetalle }: Props) {
  const idPanel = useId();
  const mejor = posicion === 1;

  return (
    <li className={`overflow-hidden rounded-3xl bg-white shadow-sm ${mejor ? 'border-2 border-campo' : 'border-2 border-transparent'}`}>
      <h3>
        <button
          type="button"
          onClick={onAlternar}
          aria-expanded={abierta}
          aria-controls={idPanel}
          className="flex w-full items-start gap-3 p-5 text-left hover:bg-campo/5 lg:p-6"
        >
          <span
            aria-hidden="true"
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full font-titulo text-lg font-black ${
              mejor ? 'bg-campo text-white' : 'bg-[#E8E1D3] text-tinta'
            }`}
          >
            {posicion}
          </span>
          <span className="flex min-w-0 flex-1 flex-col gap-1.5">
            <span className="flex flex-wrap items-center gap-2">
              <span className="sr-only">Opción {posicion}:</span>
              {mejor && (
                <span className="inline-flex items-center gap-1 rounded-full bg-hoja/25 px-3 py-0.5 text-sm font-bold text-campo">
                  <IconoInsignia tamano={16} />
                  Mejor opción
                </span>
              )}
              <span className="rounded-full bg-crema px-3 py-0.5 text-sm font-bold text-tinta">Grado {rotacion.grado}</span>
            </span>
            {!abierta && (
              <>
                <span className="text-base font-bold text-tinta">{rotacion.secuencia.map((c) => c.nombre).join(' → ')}</span>
                <span className="text-sm text-tinta/75">{textoFrecuencia(rotacion.frecuencia_exito)}</span>
              </>
            )}
            {abierta && <span className="sr-only">{rotacion.secuencia.map((c) => c.nombre).join(', luego ')}</span>}
          </span>
          <IconoChevron tamano={24} className={`mt-2 shrink-0 text-tinta/60 transition-transform ${abierta ? 'rotate-180' : ''}`} />
        </button>
      </h3>

      <div id={idPanel} hidden={!abierta} className="flex flex-col gap-4 px-5 pb-5 lg:px-6 lg:pb-6">
        <SecuenciaCultivos secuencia={rotacion.secuencia} grande />

        <p className="flex items-start gap-2 rounded-2xl bg-crema p-4 text-lg font-bold leading-snug text-tinta">
          <IconoVerificacion tamano={24} className="mt-0.5 shrink-0 text-campo" />
          {textoFrecuencia(rotacion.frecuencia_exito)}
        </p>

        <dl className="grid gap-3 sm:grid-cols-2">
          <div className="flex items-start gap-3 rounded-2xl border-2 border-borde/70 p-4">
            <IconoGota tamano={22} className="mt-0.5 shrink-0 text-agua" />
            <div>
              <dt className="text-sm font-semibold text-tinta/75">Agua que se ahorra</dt>
              <dd className="font-titulo text-xl font-extrabold text-tinta">{formatearEntero(rotacion.agua_ahorrada_m3)} m³</dd>
            </div>
          </div>
          {rotacion.aporte_nitrogeno && (
            <div className="flex items-start gap-3 rounded-2xl border-2 border-borde/70 p-4">
              <IconoBrote tamano={22} className="mt-0.5 shrink-0 text-campo" />
              <div>
                <dt className="text-sm font-semibold text-tinta/75">Abono natural para el suelo</dt>
                <dd className="text-base font-bold leading-snug text-tinta">{rotacion.aporte_nitrogeno}</dd>
              </div>
            </div>
          )}
        </dl>

        <Link
          href={hrefDetalle}
          className="flex min-h-14 items-center justify-center gap-2 rounded-full bg-campo px-6 text-base font-bold text-white shadow-sm hover:bg-[#16381F]"
        >
          Ver detalle
          <IconoFlecha tamano={20} />
        </Link>
      </div>
    </li>
  );
}
