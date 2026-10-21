// src/routes/DetalleCultivoView.tsx
// Detalle de un cultivo dentro del plan: cuándo sembrar, qué pasa si cambia el clima y por qué se
// recomienda. En celular una columna; desde 1024 px, gráficas a la izquierda y razones y botones a la derecha.
'use client';

import Link from 'next/link';
import { useState } from 'react';
import type { ErrorApi, Plan, Rotacion, VentanaSiembra } from '../api/tipos';
import { elegirRotacion } from '../api/services';
import { ErrorCard } from '../components/feedback/ErrorCard';
import { IconoAsistente, IconoAtras, IconoCheck } from '../components/iconos/Iconos';
import { Esqueleto } from '../components/inicio/Esqueleto';
import { GraficaVentanaSiembra } from '../components/plan/GraficaVentanaSiembra';
import { ListaRazones } from '../components/plan/ListaRazones';
import { MarcoPlan } from '../components/plan/MarcoPlan';
import { PanelEscenario } from '../components/plan/PanelEscenario';
import { SecuenciaCultivos } from '../components/plan/SecuenciaCultivos';
import { useDetalleCultivo } from '../hooks/useDetalleCultivo';
import { nombreCultivo, rotacionParaCultivo, textoFrecuencia } from '../lib/plan';

export interface DetalleCultivoViewProps {
  planId: string;
  cultivoId: string;
  rotacionId: string | null;
  loteId: string | null;
}

export function DetalleCultivoView({ planId, cultivoId, rotacionId, loteId }: DetalleCultivoViewProps) {
  const { estado, sinConexion, reintentar } = useDetalleCultivo(planId, cultivoId);
  const rutaPlan = loteId ? `/plan?lote=${encodeURIComponent(loteId)}` : '/plan';

  return (
    <MarcoPlan
      sinConexion={sinConexion || (estado.tipo === 'listo' && estado.ventana === null)}
      textoSinConexion={estado.tipo === 'listo' && estado.ventana === null ? 'Sin conexión. Le mostramos el último plan guardado.' : undefined}
    >
      <Link href={rutaPlan} className="inline-flex min-h-11 items-center gap-1 self-start text-base font-bold text-campo hover:underline">
        <IconoAtras tamano={20} />
        Volver al plan
      </Link>

      {estado.tipo === 'cargando' && (
        <div role="status" className="flex flex-col gap-5 lg:grid lg:grid-cols-12">
          <span className="sr-only">Cargando el detalle del cultivo…</span>
          <div className="flex flex-col gap-5 lg:col-span-7">
            <Esqueleto className="h-16 w-2/3" />
            <Esqueleto className="h-96" />
            <Esqueleto className="h-72" />
          </div>
          <Esqueleto className="h-80 lg:col-span-5" />
        </div>
      )}
      {estado.tipo === 'error' && <ErrorCard mensaje={estado.error.mensaje} onRetry={reintentar} retryLabel="Intentar de nuevo" />}
      {estado.tipo === 'listo' && (
        <Contenido
          plan={estado.plan}
          ventana={estado.ventana}
          cultivoId={cultivoId}
          rotacion={rotacionParaCultivo(estado.plan, cultivoId, rotacionId)}
          sinConexion={sinConexion || estado.ventana === null}
        />
      )}
    </MarcoPlan>
  );
}

interface ContenidoProps {
  plan: Plan;
  ventana: VentanaSiembra | null;
  cultivoId: string;
  rotacion: Rotacion | null;
  sinConexion: boolean;
}

function Contenido({ plan, ventana, cultivoId, rotacion, sinConexion }: ContenidoProps) {
  const nombre = nombreCultivo(plan, cultivoId);
  const [eleccion, setEleccion] = useState<'inicial' | 'guardando' | 'hecho'>('inicial');
  const [errorEleccion, setErrorEleccion] = useState<string | null>(null);

  if (!nombre) {
    return <ErrorCard mensaje="No encontramos ese cultivo en su plan. Vuelva al plan y elíjalo de nuevo." />;
  }

  const base = ventana ? Math.max(...ventana.puntos.map((p) => p.frecuencia_exito)) : rotacion?.frecuencia_exito ?? null;
  const razones = ventana?.razones ?? rotacion?.razones ?? [];

  const elegir = async () => {
    if (!rotacion) return;
    setEleccion('guardando');
    setErrorEleccion(null);
    try {
      await elegirRotacion(plan.id, rotacion.id);
      setEleccion('hecho');
    } catch (e) {
      setErrorEleccion((e as ErrorApi).mensaje);
      setEleccion('inicial');
    }
  };

  const consultaAsistente = new URLSearchParams({ cultivo: cultivoId, plan: plan.id });

  return (
    <>
      <header className="flex flex-col gap-2">
        <h1 className="font-titulo text-3xl font-extrabold leading-tight text-tinta lg:text-4xl">{nombre}</h1>
        {base !== null && <p className="text-lg font-semibold text-campo">{textoFrecuencia(base)} en la mejor época</p>}
        {rotacion && (
          <div className="flex flex-col gap-1">
            <p className="text-sm font-semibold text-tinta/75">Hace parte de esta rotación:</p>
            <SecuenciaCultivos secuencia={rotacion.secuencia} />
          </div>
        )}
      </header>

      <main className="flex flex-col gap-5 lg:grid lg:grid-cols-12 lg:items-start">
        <div className="flex flex-col gap-5 lg:col-span-7">
          {ventana ? (
            <GraficaVentanaSiembra ventana={ventana} nombreCultivo={nombre} />
          ) : (
            <p className="rounded-3xl bg-white p-5 text-base text-tinta/80 shadow-sm">
              La gráfica de cuándo sembrar se verá cuando vuelva la conexión.
            </p>
          )}
          <PanelEscenario planId={plan.id} cultivoId={cultivoId} nombreCultivo={nombre} base={base} desactivado={sinConexion} />
        </div>

        <div className="flex flex-col gap-5 lg:col-span-5">
          <ListaRazones razones={razones} />

          <section aria-label="Acciones" className="flex flex-col gap-3 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
            {rotacion ? (
              <button
                type="button"
                onClick={elegir}
                disabled={eleccion !== 'inicial' || sinConexion}
                className="flex min-h-14 items-center justify-center gap-2 rounded-full bg-campo px-6 text-base font-bold text-white shadow-sm hover:bg-[#16381F] disabled:opacity-70"
              >
                <IconoCheck tamano={22} />
                {eleccion === 'hecho' ? 'Plan elegido' : eleccion === 'guardando' ? 'Guardando…' : 'Elegir este plan'}
              </button>
            ) : (
              <p className="text-base text-tinta/80">Este cultivo no está en ninguna de las rotaciones recomendadas para su lote.</p>
            )}
            <Link
              href={`/asistente?${consultaAsistente.toString()}`}
              className="flex min-h-14 items-center justify-center gap-2 rounded-full border-2 border-campo/20 bg-white px-6 text-base font-bold text-campo hover:bg-campo/5"
            >
              <IconoAsistente tamano={22} />
              Preguntarle al asistente
            </Link>
            {eleccion === 'hecho' && rotacion && (
              <p role="status" className="text-base font-semibold text-campo">
                Listo. Guardamos su plan: {rotacion.secuencia.map((c) => c.nombre).join(', luego ')}.
              </p>
            )}
            {errorEleccion && (
              <p role="alert" className="text-base font-semibold text-[#B23B3B]">
                No pudimos guardar su elección: {errorEleccion}
              </p>
            )}
            {sinConexion && eleccion !== 'hecho' && rotacion && (
              <p className="text-base text-tinta/80">Sin conexión no podemos guardar su elección.</p>
            )}
          </section>
        </div>
      </main>
    </>
  );
}
