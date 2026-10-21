// src/routes/FichaLoteView.tsx
// Ficha del lote PROVISIONAL: datos del lote y recomendación de cultivos del modelo predictivo.
// Funciona de punta a punta mientras el equipo diseña la versión final en Stitch.
'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ErrorCard } from '../components/feedback/ErrorCard';
import type { CultivoRecomendado, ErrorApi, EstadoModelo, LoteDetalle, RecomendacionResponse } from '../api/tipos';
import { obtenerEstadoModelo, obtenerLote, obtenerRecomendacion, solicitarRecomendacion } from '../api/services';

const INTERVALO_CONSULTA_MS = 3000;
const formatoFecha = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
const numero = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });

const fecha = (iso: string) => formatoFecha.format(new Date(`${iso}T00:00:00Z`));

function textoEnso(oni: number | null | undefined): string | null {
  if (oni == null) return null;
  if (oni >= 0.5) return `El Niño (ONI ${oni.toFixed(1).replace('.', ',')}): suele traer menos lluvia`;
  if (oni <= -0.5) return `La Niña (ONI ${oni.toFixed(1).replace('.', ',')}): suele traer más lluvia`;
  return 'Sin El Niño ni La Niña';
}

const TarjetaCultivo: React.FC<{ c: CultivoRecomendado; puesto: number }> = ({ c, puesto }) => (
  <li className="rounded-2xl border-2 border-[#D2C8B5] bg-white p-4 flex flex-col gap-2">
    <div className="flex items-baseline justify-between gap-3">
      <h3 className="text-lg font-black text-[#14202B]">
        {puesto}. {c.cultivo}
      </h3>
      <span className="text-sm font-bold text-[#1F4D2B] whitespace-nowrap">{c.de_cada_10} de cada 10 años</span>
    </div>
    {/* Idoneidad esperada con su rango (escenario malo a bueno) */}
    <div className="relative h-3 rounded-full bg-[#E8E1D3]" aria-label={`Idoneidad ${Math.round(c.puntaje * 100)} de 100`}>
      <div
        className="absolute inset-y-0 rounded-full bg-[#6DBE7A]/45"
        style={{ left: `${c.puntaje_min * 100}%`, width: `${Math.max(c.puntaje_max - c.puntaje_min, 0.01) * 100}%` }}
      />
      <div className="absolute inset-y-0 left-0 rounded-full bg-[#1F4D2B]" style={{ width: `${c.puntaje * 100}%` }} />
    </div>
    <p className="text-sm text-[#14202B]/80">
      {c.riego_bruto_m3_ha != null
        ? `Riego en todo el ciclo: unos ${numero.format(c.riego_bruto_m3_ha)} m³ por hectárea`
        : 'Todavía no tenemos datos de agua para este cultivo'}
      {' · '}
      {c.dias_ciclo} días de ciclo
    </p>
  </li>
);

export const FichaLoteView: React.FC<{ loteId: string; onIngresar: () => void }> = ({ loteId, onIngresar }) => {
  const [lote, setLote] = useState<LoteDetalle | null>(null);
  const [modelo, setModelo] = useState<EstadoModelo | null>(null);
  const [error, setError] = useState<ErrorApi | null>(null);
  const [recomendacion, setRecomendacion] = useState<RecomendacionResponse | null>(null);
  const [pidiendo, setPidiendo] = useState(false);
  const temporizador = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    let cancelado = false;
    Promise.all([obtenerLote(loteId), obtenerEstadoModelo()])
      .then(([l, m]) => {
        if (cancelado) return;
        setLote(l);
        setModelo(m);
      })
      .catch((e: ErrorApi) => !cancelado && setError(e));
    return () => {
      cancelado = true;
      clearTimeout(temporizador.current);
    };
  }, [loteId]);

  const consultar = useCallback(
    async (id: string) => {
      try {
        const r = await obtenerRecomendacion(loteId, id);
        setRecomendacion(r);
        if (r.estado === 'en_proceso') temporizador.current = setTimeout(() => void consultar(id), INTERVALO_CONSULTA_MS);
        else setPidiendo(false);
      } catch (e) {
        setError(e as ErrorApi);
        setPidiendo(false);
      }
    },
    [loteId]
  );

  const pedir = async () => {
    setError(null);
    setPidiendo(true);
    setRecomendacion(null);
    try {
      const { recomendacion_id } = await solicitarRecomendacion(loteId);
      await consultar(recomendacion_id);
    } catch (e) {
      setError(e as ErrorApi);
      setPidiendo(false);
    }
  };

  const sinSesion = error?.codigo === 'AUTH_NO_AUTENTICADO';

  return (
    <main className="min-h-dvh bg-[#F7F3EA] text-[#14202B]">
      <div className="max-w-xl mx-auto px-4 py-6 flex flex-col gap-5">
        {error && (
          <ErrorCard
            mensaje={error.mensaje}
            codigo={error.codigo}
            onRetry={sinSesion ? onIngresar : undefined}
            retryLabel={sinSesion ? 'Ingresar' : undefined}
          />
        )}

        {lote && (
          <header className="flex flex-col gap-1">
            <p className="text-sm font-bold uppercase tracking-wider text-[#1F4D2B]">{lote.finca_nombre}</p>
            <h1 className="font-titulo text-3xl font-black text-[#14202B]">{lote.nombre}</h1>
            <p className="text-base text-[#14202B]/80">
              {lote.area_ha.toFixed(1).replace('.', ',')} ha en {lote.corregimiento_nombre}, {lote.municipio_nombre}
              {' · '}
              {lote.tiene_riego ? 'con riego' : 'solo lluvia'}
            </p>
          </header>
        )}

        {lote && modelo && (
          <section aria-labelledby="titulo-recomendacion" className="flex flex-col gap-4">
            <h2 id="titulo-recomendacion" className="font-titulo text-2xl font-black text-[#1F4D2B]">
              ¿Qué me conviene sembrar?
            </h2>

            {!modelo.disponible ? (
              <p className="rounded-2xl bg-[#E8E1D3] p-4 text-base">
                La recomendación de cultivos todavía no está activa en este servidor. Su lote y el diagnóstico ya
                quedaron guardados.
              </p>
            ) : (
              !recomendacion?.cultivos.length && (
                <button
                  type="button"
                  onClick={pedir}
                  disabled={pidiendo}
                  className="min-h-14 rounded-2xl bg-[#1F4D2B] px-6 font-titulo text-lg font-extrabold text-white shadow-md hover:bg-[#16381F] disabled:opacity-70"
                >
                  {pidiendo ? 'Calculando…' : 'Ver qué me conviene sembrar'}
                </button>
              )
            )}

            {recomendacion && (
              <p role="status" aria-live="polite" className="text-base text-[#14202B]/80">
                {recomendacion.estado === 'lista'
                  ? `Si siembra el ${fecha(recomendacion.fecha_siembra)}:`
                  : recomendacion.mensaje}
              </p>
            )}

            {recomendacion?.estado === 'lista' && (
              <>
                <ol className="flex flex-col gap-3">
                  {recomendacion.cultivos.map((c, i) => (
                    <TarjetaCultivo key={c.id} c={c} puesto={i + 1} />
                  ))}
                </ol>

                {recomendacion.contexto && (
                  <ul className="rounded-2xl bg-[#EAF1FB] p-4 text-sm flex flex-col gap-1">
                    {textoEnso(recomendacion.contexto.oni) && <li>{textoEnso(recomendacion.contexto.oni)}</li>}
                    {recomendacion.contexto.lluvia_90_dias_mm != null && (
                      <li>Lluvia de los últimos 90 días: {numero.format(recomendacion.contexto.lluvia_90_dias_mm)} mm</li>
                    )}
                    <li>
                      Altitud {numero.format(recomendacion.contexto.elevacion_m)} m
                      {recomendacion.contexto.ph_0_30 != null &&
                        ` · pH del suelo ${recomendacion.contexto.ph_0_30.toFixed(1).replace('.', ',')}`}
                    </li>
                  </ul>
                )}

                {recomendacion.descartados.length > 0 && (
                  <details className="rounded-2xl border-2 border-[#D2C8B5] bg-white p-4">
                    <summary className="min-h-11 cursor-pointer font-bold">
                      {recomendacion.descartados.length} cultivos no se dan en su lote
                    </summary>
                    <ul className="mt-2 flex flex-col gap-1 text-sm text-[#14202B]/80">
                      {recomendacion.descartados.map((d) => (
                        <li key={d.id}>
                          <span className="font-semibold text-[#14202B]">{d.cultivo}</span>: {d.motivo}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </>
            )}

            {recomendacion?.estado === 'fallida' && (
              <button
                type="button"
                onClick={pedir}
                className="min-h-14 rounded-2xl bg-[#E8833A] px-6 font-titulo text-lg font-extrabold text-white hover:bg-[#C96D27]"
              >
                Intentar de nuevo
              </button>
            )}
          </section>
        )}
      </div>
    </main>
  );
};
