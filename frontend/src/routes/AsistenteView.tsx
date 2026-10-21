// src/routes/AsistenteView.tsx
// Pantalla del Asistente SURCO. En celular: encabezado, conversación y la barra de entrada encima
// del menú inferior. En escritorio: menú a la izquierda, chat al centro y resumen del lote a la derecha.
// El micrófono vive solo en la barra de entrada (aquí no va el botón flotante).
'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { ErrorApi, LoteResumen } from '../api/tipos';
import { listarMisLotes, obtenerPlan } from '../api/services';
import { AvisoMicrofono } from '../components/asistente/AvisoMicrofono';
import { BarraEntrada } from '../components/asistente/BarraEntrada';
import { BienvenidaAsistente, PreguntasSugeridas } from '../components/asistente/BienvenidaAsistente';
import { BurbujaAsistente } from '../components/asistente/BurbujaAsistente';
import { BurbujaProductor } from '../components/asistente/BurbujaProductor';
import { EncabezadoAsistente } from '../components/asistente/EncabezadoAsistente';
import { IndicadorPensando } from '../components/asistente/IndicadorPensando';
import { PanelLote } from '../components/asistente/PanelLote';
import { ErrorCard } from '../components/feedback/ErrorCard';
import { FranjaSinConexion } from '../components/feedback/FranjaSinConexion';
import { IconoChevron } from '../components/iconos/Iconos';
import { Esqueleto } from '../components/inicio/Esqueleto';
import { NavegacionPrincipal } from '../components/inicio/NavegacionPrincipal';
import { useAutoScroll } from '../hooks/useAutoScroll';
import { useConversacion } from '../hooks/useConversacion';
import { useGrabadora } from '../hooks/useGrabadora';
import { preguntasSugeridas } from '../lib/asistente';
import { nombreCultivo } from '../lib/plan';

export interface AsistenteViewProps {
  lotePedido: string | null;
  /** Si llega desde el Plan de siembra: el cultivo y el plan de donde viene. */
  cultivoId: string | null;
  planId: string | null;
  onCambiarLote: (loteId: string) => void;
}

type EstadoLotes = { tipo: 'cargando' } | { tipo: 'listo'; lotes: LoteResumen[] } | { tipo: 'error'; error: ErrorApi };

export function AsistenteView({ lotePedido, cultivoId, planId, onCambiarLote }: AsistenteViewProps) {
  const [lotes, setLotes] = useState<EstadoLotes>({ tipo: 'cargando' });
  const [intentoLotes, setIntentoLotes] = useState(0);
  const [cultivo, setCultivo] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setLotes({ tipo: 'cargando' });
    listarMisLotes()
      .then((l) => !cancelado && setLotes({ tipo: 'listo', lotes: l }))
      .catch((e: ErrorApi) => !cancelado && setLotes({ tipo: 'error', error: e }));
    return () => {
      cancelado = true;
    };
  }, [intentoLotes]);

  // El nombre del cultivo que trae el Plan, para sugerir "¿Por qué me recomiendan …?"
  useEffect(() => {
    if (!cultivoId || !planId) return;
    let cancelado = false;
    obtenerPlan(planId)
      .then((plan) => !cancelado && setCultivo(nombreCultivo(plan, cultivoId)))
      .catch(() => undefined);
    return () => {
      cancelado = true;
    };
  }, [cultivoId, planId]);

  const listaLotes = lotes.tipo === 'listo' ? lotes.lotes : [];
  const loteId = listaLotes.find((l) => l.id === lotePedido)?.id ?? listaLotes[0]?.id ?? null;
  const conversacion = useConversacion(loteId);
  const { estado, error, nombre, mensajes, pensando, sinConexion, enviarTexto, enviarAudio, reintentarEnvio, valorar, recargar } = conversacion;
  const grabadora = useGrabadora(enviarAudio);

  const ultimo = mensajes[mensajes.length - 1];
  const { contenedor, hayNuevos, irAlFinal, alDesplazar } = useAutoScroll(
    `${estado}-${mensajes.length}-${pensando}-${ultimo?.envio ?? ''}-${ultimo?.texto.length ?? 0}`
  );

  const sugeridas = preguntasSugeridas(cultivo);
  const preguntaCultivo = cultivo ? sugeridas[0] : null;
  const yaPreguntoCultivo = preguntaCultivo !== null && mensajes.some((m) => m.rol === 'productor' && m.texto === preguntaCultivo);
  const sinLotes = lotes.tipo === 'listo' && listaLotes.length === 0;
  const listo = estado === 'listo' && loteId !== null;
  const entradaBloqueada = !listo || sinLotes;

  return (
    <div className="flex h-dvh flex-col bg-crema text-tinta lg:pl-64">
      {sinConexion && <FranjaSinConexion />}

      <div className="flex min-h-0 flex-1 lg:grid lg:grid-cols-[minmax(0,1fr)_24rem]">
        <section aria-label="Chat con el Asistente SURCO" className="relative flex min-h-0 min-w-0 flex-1 flex-col">
          <EncabezadoAsistente lotes={listaLotes} loteId={loteId} onCambiarLote={onCambiarLote} />

          <div ref={contenedor} onScroll={alDesplazar} className="min-h-0 flex-1 overflow-y-auto">
            <div role="log" aria-live="polite" aria-label="Conversación" className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-5">
              {(lotes.tipo === 'cargando' || (loteId && estado === 'cargando')) && (
                <div role="status" className="flex flex-col gap-4">
                  <span className="sr-only">Cargando la conversación…</span>
                  <Esqueleto className="ml-auto h-20 w-3/5" />
                  <Esqueleto className="h-40 w-4/5" />
                </div>
              )}
              {lotes.tipo === 'error' && (
                <ErrorCard mensaje={lotes.error.mensaje} onRetry={() => setIntentoLotes((n) => n + 1)} retryLabel="Intentar de nuevo" />
              )}
              {sinLotes && (
                <div className="flex flex-col items-start gap-3 rounded-3xl bg-white p-5 shadow-sm">
                  <p className="text-lg font-bold text-tinta">Para responderle con datos, primero marque su lote.</p>
                  <Link href="/mis-lotes" className="flex min-h-14 items-center rounded-full bg-campo px-6 text-base font-bold text-white">
                    Marcar mi lote
                  </Link>
                </div>
              )}
              {estado === 'error' && error && loteId && <ErrorCard mensaje={error.mensaje} onRetry={recargar} retryLabel="Intentar de nuevo" />}

              {listo && mensajes.length === 0 && (
                <BienvenidaAsistente nombre={nombre} preguntas={sugeridas} onPreguntar={enviarTexto} desactivado={sinConexion || pensando} />
              )}

              {listo &&
                mensajes.map((m) =>
                  m.rol === 'productor' ? (
                    <BurbujaProductor key={m.id} mensaje={m} onReintentar={reintentarEnvio} puedeReintentar={!sinConexion && !pensando} />
                  ) : (
                    <BurbujaAsistente key={m.id} mensaje={m} onValorar={valorar} desactivado={sinConexion} />
                  )
                )}

              {pensando && <IndicadorPensando />}

              {listo && mensajes.length > 0 && preguntaCultivo && !yaPreguntoCultivo && !pensando && (
                <PreguntasSugeridas preguntas={[preguntaCultivo]} onPreguntar={enviarTexto} desactivado={sinConexion} />
              )}
            </div>
          </div>

          {hayNuevos && (
            <button
              type="button"
              onClick={irAlFinal}
              className="absolute bottom-48 left-1/2 flex min-h-14 -translate-x-1/2 items-center gap-2 rounded-full bg-tinta px-5 text-base font-bold text-white shadow-lg"
            >
              <IconoChevron tamano={20} />
              Ver mensajes nuevos
            </button>
          )}

          <div className="border-t border-borde/70 bg-crema px-4 pt-2 pb-3">
            <div className="mx-auto flex w-full max-w-3xl flex-col gap-2">
              <AvisoMicrofono estado={grabadora.estado} onPermitir={() => void grabadora.iniciar()} onCerrar={grabadora.descartarAviso} />
              <BarraEntrada
                grabadora={grabadora}
                sinConexion={sinConexion}
                pensando={pensando || entradaBloqueada}
                onEnviarTexto={enviarTexto}
              />
            </div>
          </div>
        </section>

        <div className="hidden min-h-0 overflow-y-auto border-l border-borde/70 bg-white lg:block">{loteId && <PanelLote loteId={loteId} />}</div>
      </div>

      {/* Lugar del menú inferior en celular, para que no tape la barra de entrada */}
      <div aria-hidden="true" className="h-[calc(4rem+1px+env(safe-area-inset-bottom))] shrink-0 lg:hidden" />
      <NavegacionPrincipal />
    </div>
  );
}
