// src/routes/PlanView.tsx
// Pantalla Plan del lote. Un solo árbol responsivo: en celular una columna (rotaciones, ranking y
// lluvias) y desde 1024 px dos columnas (rotaciones y lluvias a la izquierda, ranking a la derecha).
'use client';

import { useState } from 'react';
import type { ErrorApi, LluviaMensual, LoteResumen, Plan } from '../api/tipos';
import { iniciarDiagnostico } from '../api/services';
import { ErrorCard } from '../components/feedback/ErrorCard';
import { TaskProgress } from '../components/feedback/TaskProgress';
import { CalendarioLluvias } from '../components/plan/CalendarioLluvias';
import { MarcoPlan } from '../components/plan/MarcoPlan';
import { EsqueletoPlan, SinDiagnostico, SinLotes, SinPlan } from '../components/plan/EstadoPlan';
import { ListaRanking } from '../components/plan/ListaRanking';
import { SelectorLote } from '../components/plan/SelectorLote';
import { TarjetaRotacion } from '../components/plan/TarjetaRotacion';
import { usePlanLote } from '../hooks/usePlanLote';
import { formatearDiaMes, formatearUnDecimal } from '../lib/fechas';

export interface PlanViewProps {
  lotePedido: string | null;
  onCambiarLote: (loteId: string) => void;
  onNavigate: (ruta: string) => void;
}

/** Ruta del detalle de un cultivo; lleva la rotación (si viene de una) y el lote para volver. */
export function rutaDetalle(planId: string, cultivoId: string, loteId: string, rotacionId?: string): string {
  const consulta = new URLSearchParams({ lote: loteId });
  if (rotacionId) consulta.set('rotacion', rotacionId);
  return `/plan/${encodeURIComponent(planId)}/cultivo/${encodeURIComponent(cultivoId)}?${consulta.toString()}`;
}

export function PlanView({ lotePedido, onCambiarLote, onNavigate }: PlanViewProps) {
  const { lotes, loteId, estado, sinConexion, armando, errorArmar, reintentar, armarPlan, verPlanCalculado } = usePlanLote(lotePedido);
  const [analizando, setAnalizando] = useState(false);
  const [errorAnalizar, setErrorAnalizar] = useState<string | null>(null);
  const lote = lotes.find((l) => l.id === loteId) ?? null;

  const analizarLote = async () => {
    if (!loteId) return;
    setAnalizando(true);
    setErrorAnalizar(null);
    try {
      const { tarea_id } = await iniciarDiagnostico(loteId);
      onNavigate(`/lotes/${encodeURIComponent(loteId)}?tarea=${encodeURIComponent(tarea_id)}`);
    } catch (e) {
      setErrorAnalizar((e as ErrorApi).mensaje);
      setAnalizando(false);
    }
  };

  const desdeGuardado = estado.tipo === 'listo' && estado.desdeGuardado;

  if (estado.tipo === 'calculando') {
    return (
      <MarcoPlan sinConexion={sinConexion}>
        {estado.tarea ? (
          <TaskProgress
            tarea={estado.tarea}
            onCompletado={verPlanCalculado}
            onReintentar={armarPlan}
            textos={{
              titulo: 'Estamos armando su plan de siembra',
              tituloListo: 'Su plan de siembra está listo',
              descripcion: lote
                ? `Comparamos 40 años de clima de ${lote.nombre} (${formatearUnDecimal(lote.area_ha)} ha) y el pronóstico de El Niño y La Niña.`
                : 'Comparamos 40 años de clima de su zona y el pronóstico de El Niño y La Niña.',
              botonListo: 'Ver mi plan',
              anuncioListo: 'Su plan de siembra está listo.',
              anuncioFallido: 'No pudimos terminar su plan de siembra.',
              nombreProgreso: 'Progreso del plan'
            }}
          />
        ) : (
          <p role="status" className="py-10 text-center text-base font-semibold text-tinta/70">
            Estamos armando su plan de siembra…
          </p>
        )}
      </MarcoPlan>
    );
  }

  return (
    <MarcoPlan
      sinConexion={sinConexion || desdeGuardado}
      textoSinConexion={
        estado.tipo === 'listo' && desdeGuardado
          ? `Sin conexión. Le mostramos el último plan guardado, del ${formatearDiaMes(estado.plan.calculado_en)}.`
          : undefined
      }
    >
      <header className="flex flex-col gap-3">
        <h1 className="font-titulo text-3xl font-extrabold leading-tight text-tinta lg:text-4xl">Plan de siembra</h1>
        <SelectorLote lotes={lotes} loteId={loteId} onCambiar={onCambiarLote} />
        <p className="max-w-2xl text-base leading-relaxed text-tinta/80">
          Analizamos 40 años de clima de su zona y el pronóstico de El Niño y La Niña.
        </p>
      </header>

      {estado.tipo === 'cargando' && <EsqueletoPlan />}
      {estado.tipo === 'error' && (
        <ErrorCard mensaje={estado.error.mensaje} onRetry={reintentar} retryLabel="Intentar de nuevo" />
      )}
      {estado.tipo === 'sin_lotes' && <SinLotes />}
      {estado.tipo === 'sin_diagnostico' && <SinDiagnostico onAccion={analizarLote} ocupado={analizando} error={errorAnalizar} />}
      {estado.tipo === 'sin_plan' && (
        <SinPlan onAccion={armarPlan} ocupado={armando} error={sinConexion ? 'Sin conexión no podemos armar el plan.' : errorArmar} />
      )}
      {estado.tipo === 'listo' && lote && <ContenidoPlan plan={estado.plan} lluvias={estado.lluvias} lote={lote} />}
    </MarcoPlan>
  );
}

function ContenidoPlan({ plan, lluvias, lote }: { plan: Plan; lluvias: LluviaMensual[] | null; lote: LoteResumen }) {
  const [abierta, setAbierta] = useState<string | null>(plan.rotaciones[0]?.id ?? null);
  const rotaciones = plan.rotaciones.slice(0, 3);

  return (
    <main className="flex flex-col gap-5 lg:grid lg:grid-cols-12 lg:items-start">
      <div className="contents lg:col-span-7 lg:flex lg:flex-col lg:gap-5">
        <section aria-labelledby="titulo-rotaciones" className="order-1 flex flex-col gap-3 lg:order-none">
          <h2 id="titulo-rotaciones" className="font-titulo text-2xl font-extrabold text-tinta">
            Las {rotaciones.length} mejores rotaciones para su lote
          </h2>
          <ol className="flex flex-col gap-3">
            {rotaciones.map((r, i) => (
              <TarjetaRotacion
                key={r.id}
                rotacion={r}
                posicion={i + 1}
                abierta={abierta === r.id}
                onAlternar={() => setAbierta((actual) => (actual === r.id ? null : r.id))}
                hrefDetalle={rutaDetalle(plan.id, r.secuencia[0]?.cultivo_id ?? '', lote.id, r.id)}
              />
            ))}
          </ol>
        </section>
        {lluvias && (
          <div className="order-3 lg:order-none">
            <CalendarioLluvias meses={lluvias} />
          </div>
        )}
      </div>

      <div className="contents lg:col-span-5 lg:flex lg:flex-col lg:gap-5">
        <div className="order-2 lg:order-none">
          <ListaRanking ranking={plan.ranking} hrefCultivo={(cultivoId) => rutaDetalle(plan.id, cultivoId, lote.id)} />
        </div>
      </div>
    </main>
  );
}
