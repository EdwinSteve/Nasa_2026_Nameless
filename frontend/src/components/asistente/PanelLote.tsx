// Panel derecho (escritorio): resumen del lote con el que responde el asistente.
'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { ResumenLote } from '../../api/tipos';
import { obtenerResumenLote } from '../../api/services';
import { formatearEntero, formatearUnDecimal } from '../../lib/fechas';
import { IconoFlecha, IconoUbicacion } from '../iconos/Iconos';
import { Esqueleto } from '../inicio/Esqueleto';
import { EtapasCultivo } from '../inicio/EtapasCultivo';
import { IndicadoresLote } from '../inicio/IndicadoresLote';

type Estado = { tipo: 'cargando' } | { tipo: 'listo'; lote: ResumenLote } | { tipo: 'error' };

export function PanelLote({ loteId }: { loteId: string }) {
  const [estado, setEstado] = useState<Estado>({ tipo: 'cargando' });

  useEffect(() => {
    let cancelado = false;
    setEstado({ tipo: 'cargando' });
    obtenerResumenLote(loteId)
      .then((lote) => !cancelado && setEstado({ tipo: 'listo', lote }))
      .catch(() => !cancelado && setEstado({ tipo: 'error' }));
    return () => {
      cancelado = true;
    };
  }, [loteId]);

  return (
    <aside aria-label="Resumen del lote" className="flex flex-col gap-4 p-5">
      {estado.tipo === 'cargando' && (
        <div role="status" className="flex flex-col gap-3">
          <span className="sr-only">Cargando el resumen del lote…</span>
          <Esqueleto className="h-14" />
          <Esqueleto className="h-40" />
          <Esqueleto className="h-48" />
        </div>
      )}
      {estado.tipo === 'error' && <p className="text-base text-tinta/75">No pudimos cargar el resumen de este lote.</p>}
      {estado.tipo === 'listo' && (
        <>
          <div>
            <h2 className="font-titulo text-xl font-extrabold text-tinta">{estado.lote.nombre}</h2>
            <p className="flex items-start gap-1 text-base text-tinta/75">
              <IconoUbicacion tamano={18} className="mt-0.5 shrink-0 text-sol" />
              <span>
                {formatearUnDecimal(estado.lote.area_ha)} ha · {estado.lote.corregimiento_nombre}
                {estado.lote.altitud_msnm != null && ` · ${formatearEntero(estado.lote.altitud_msnm)} m`}
              </span>
            </p>
          </div>
          {estado.lote.cultivo ? (
            <EtapasCultivo cultivo={estado.lote.cultivo} />
          ) : (
            <p className="rounded-2xl bg-crema p-3 text-base text-tinta">Este lote todavía no tiene un cultivo registrado.</p>
          )}
          <IndicadoresLote indicadores={estado.lote.indicadores} />
          <Link
            href={`/lotes/${encodeURIComponent(estado.lote.id)}`}
            className="flex min-h-14 items-center justify-center gap-2 rounded-full border-2 border-campo/20 px-5 text-base font-bold text-campo hover:bg-campo/5"
          >
            Ver en mi lote
            <IconoFlecha tamano={18} />
          </Link>
        </>
      )}
    </aside>
  );
}
