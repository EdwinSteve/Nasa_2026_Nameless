// "Hoy le recomendamos": el mensaje del backend, su porqué y "Ya regué".
'use client';

import { useId, useState, type ReactNode } from 'react';
import type { ErrorApi, ResumenInicio } from '../../api/tipos';
import { registrarRiego } from '../../api/services';
import { IconoAlerta, IconoAyuda, IconoBrote, IconoCheck, IconoCosecha, IconoGota } from '../iconos/Iconos';
import { ChipFuente } from './ChipFuente';

type Recomendacion = NonNullable<ResumenInicio['recomendacion_hoy']>;

const ICONO: Record<Recomendacion['tipo'], ReactNode> = {
  riego: <IconoGota tamano={24} />,
  siembra: <IconoBrote tamano={24} />,
  cosecha: <IconoCosecha tamano={24} />,
  alerta: <IconoAlerta tamano={24} />,
  ninguna: <IconoCheck tamano={24} />
};

/** Resalta las cantidades de agua ("450 m³") que vengan en el mensaje del backend. */
function conCantidadesResaltadas(mensaje: string): ReactNode[] {
  return mensaje.split(/(\d[\d.,]*\s?m³)/).map((parte, i) =>
    i % 2 === 1 ? (
      <span key={i} className="font-black text-[#B5601F]">
        {parte}
      </span>
    ) : (
      parte
    )
  );
}

interface Props {
  recomendacion: ResumenInicio['recomendacion_hoy'];
  loteId: string | null;
  puedeRegistrarRiego: boolean;
}

export function TarjetaRecomendacion({ recomendacion, loteId, puedeRegistrarRiego }: Props) {
  const idTitulo = useId();
  const idPorque = useId();
  const [verPorque, setVerPorque] = useState(false);
  const [riego, setRiego] = useState<'inicial' | 'guardando' | 'hecho'>('inicial');
  const [errorRiego, setErrorRiego] = useState<string | null>(null);

  const hayAlgo = recomendacion !== null && recomendacion.tipo !== 'ninguna';

  const anotarRiego = async () => {
    if (!loteId) return;
    setRiego('guardando');
    setErrorRiego(null);
    try {
      await registrarRiego(loteId);
      setRiego('hecho');
    } catch (e) {
      setErrorRiego((e as ErrorApi).mensaje);
      setRiego('inicial');
    }
  };

  return (
    <section aria-labelledby={idTitulo} className="relative flex flex-col gap-4 overflow-hidden rounded-3xl bg-white p-5 shadow-md lg:p-6">
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-1.5 bg-sol" />
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-sol/15 text-[#B5601F]">
            {ICONO[hayAlgo && recomendacion ? recomendacion.tipo : 'ninguna']}
          </span>
          <h2 id={idTitulo} className="font-titulo text-xl font-extrabold text-tinta">
            Hoy le recomendamos
          </h2>
        </div>
        {recomendacion && <ChipFuente procedencia={recomendacion.procedencia} />}
      </div>

      {!hayAlgo || !recomendacion ? (
        <div className="rounded-2xl bg-crema p-4">
          <p className="text-xl font-bold leading-snug text-tinta">Hoy su cultivo no necesita nada especial.</p>
          <p className="mt-1 text-base text-tinta/75">Le avisaremos cuando haya algo que hacer en su lote.</p>
        </div>
      ) : (
        <>
          <p className="rounded-2xl bg-crema p-4 text-xl font-bold leading-snug text-tinta">
            {conCantidadesResaltadas(recomendacion.mensaje)}
          </p>

          <div className={`grid gap-3 ${puedeRegistrarRiego ? 'grid-cols-2' : 'grid-cols-1'}`}>
            {puedeRegistrarRiego && (
              <button
                type="button"
                onClick={anotarRiego}
                disabled={riego !== 'inicial'}
                aria-live="polite"
                className="flex min-h-14 items-center justify-center gap-2 rounded-full bg-campo px-4 text-base font-bold text-white shadow-sm hover:bg-[#16381F] disabled:opacity-80"
              >
                <IconoCheck tamano={22} />
                {riego === 'hecho' ? 'Riego anotado' : riego === 'guardando' ? 'Anotando…' : 'Ya regué'}
              </button>
            )}
            <button
              type="button"
              onClick={() => setVerPorque((v) => !v)}
              aria-expanded={verPorque}
              aria-controls={idPorque}
              className="flex min-h-14 items-center justify-center gap-2 rounded-full border-2 border-campo/20 bg-white px-4 text-base font-bold text-campo hover:bg-campo/5"
            >
              <IconoAyuda tamano={22} />
              ¿Por qué?
            </button>
          </div>

          {riego === 'hecho' && (
            <p role="status" className="text-base font-semibold text-campo">
              Listo. Anotamos su riego de hoy.
            </p>
          )}
          {errorRiego && (
            <p role="alert" className="text-base font-semibold text-[#B23B3B]">
              No pudimos anotar el riego: {errorRiego}
            </p>
          )}
          <div id={idPorque} hidden={!verPorque} className="rounded-2xl border-2 border-borde p-4 text-base leading-relaxed text-tinta">
            {recomendacion.detalle_porque}
          </div>
        </>
      )}
    </section>
  );
}
