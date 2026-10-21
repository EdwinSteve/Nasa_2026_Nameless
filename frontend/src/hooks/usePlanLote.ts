// src/hooks/usePlanLote.ts
// Datos de la pantalla Plan del lote: lotes, último plan, lluvias, tarea en curso y copia sin conexión.
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { ErrorApi, LluviaMensual, LoteResumen, Plan, TareaPlanResponse } from '../api/tipos';
import {
  generarPlan,
  listarMisLotes,
  obtenerLluviasEsperadas,
  obtenerPlan,
  obtenerTareaPlan,
  obtenerUltimoPlan
} from '../api/services';
import { guardarPlan, leerPlanGuardado } from '../lib/planGuardado';
import { tareaEnCurso } from '../lib/plan';
import { useSinConexion } from './useResumenInicio';

export const INTERVALO_TAREA_MS = 1500;

export type EstadoPlan =
  | { tipo: 'cargando' }
  | { tipo: 'sin_lotes' }
  | { tipo: 'sin_diagnostico' }
  | { tipo: 'sin_plan' }
  | { tipo: 'calculando'; tareaId: string; tarea: TareaPlanResponse | null }
  | { tipo: 'listo'; plan: Plan; lluvias: LluviaMensual[] | null; desdeGuardado: boolean }
  | { tipo: 'error'; error: ErrorApi };

export interface UsePlanLote {
  lotes: LoteResumen[];
  loteId: string | null;
  estado: EstadoPlan;
  sinConexion: boolean;
  /** true mientras se pide armar el plan (antes de que llegue la tarea). */
  armando: boolean;
  errorArmar: string | null;
  reintentar: () => void;
  armarPlan: () => void;
  /** Al terminar la tarea: carga el plan recién armado. */
  verPlanCalculado: () => void;
}

/** Qué mostrar según el error al pedir el último plan. Exportada para las pruebas. */
export function estadoPorError(error: ErrorApi, loteId: string): EstadoPlan {
  if (error.codigo === 'PLAN_NO_DISPONIBLE') return { tipo: 'sin_plan' };
  if (error.codigo === 'DIAGNOSTICO_NO_DISPONIBLE') return { tipo: 'sin_diagnostico' };
  const tareaId = tareaEnCurso(error);
  if (tareaId) return { tipo: 'calculando', tareaId, tarea: null };
  if (error.codigo === 'RED_SIN_CONEXION') {
    const guardado = leerPlanGuardado(loteId);
    if (guardado) return { tipo: 'listo', plan: guardado.plan, lluvias: guardado.lluvias, desdeGuardado: true };
  }
  return { tipo: 'error', error };
}

export function usePlanLote(lotePedido: string | null): UsePlanLote {
  const [lotes, setLotes] = useState<LoteResumen[]>([]);
  const [lotesListos, setLotesListos] = useState(false);
  const [estado, setEstado] = useState<EstadoPlan>({ tipo: 'cargando' });
  const [intento, setIntento] = useState(0);
  const [armando, setArmando] = useState(false);
  const [errorArmar, setErrorArmar] = useState<string | null>(null);
  const sinConexion = useSinConexion();

  const loteId = lotes.find((l) => l.id === lotePedido)?.id ?? lotes[0]?.id ?? null;

  // 1. Los lotes del usuario
  useEffect(() => {
    let cancelado = false;
    setEstado({ tipo: 'cargando' });
    listarMisLotes()
      .then((respuesta) => {
        if (cancelado) return;
        setLotes(respuesta);
        setLotesListos(true);
        if (respuesta.length === 0) setEstado({ tipo: 'sin_lotes' });
      })
      .catch((e: ErrorApi) => {
        if (!cancelado) setEstado({ tipo: 'error', error: e });
      });
    return () => {
      cancelado = true;
    };
  }, [intento]);

  // 2. El último plan del lote elegido, con sus lluvias
  useEffect(() => {
    if (!lotesListos || !loteId) return;
    let cancelado = false;
    setEstado({ tipo: 'cargando' });
    setErrorArmar(null);
    Promise.all([obtenerUltimoPlan(loteId), obtenerLluviasEsperadas(loteId).catch(() => null)])
      .then(([plan, lluvias]) => {
        if (cancelado) return;
        guardarPlan(loteId, { plan, lluvias });
        setEstado({ tipo: 'listo', plan, lluvias, desdeGuardado: false });
      })
      .catch((e: ErrorApi) => {
        if (!cancelado) setEstado(estadoPorError(e, loteId));
      });
    return () => {
      cancelado = true;
    };
  }, [lotesListos, loteId, intento]);

  // 3. Mientras se arma el plan, se consulta la tarea cada INTERVALO_TAREA_MS hasta que termine
  const tareaId = estado.tipo === 'calculando' ? estado.tareaId : null;
  useEffect(() => {
    if (!tareaId || !loteId) return;
    let cancelado = false;
    let temporizador: ReturnType<typeof setTimeout> | undefined;
    const consultar = async () => {
      try {
        const tarea = await obtenerTareaPlan(loteId, tareaId);
        if (cancelado) return;
        setEstado({ tipo: 'calculando', tareaId, tarea });
        if (tarea.estado === 'lista' || tarea.estado === 'fallida') return;
      } catch (e) {
        if (cancelado) return;
        if ((e as ErrorApi).codigo !== 'RED_SIN_CONEXION') {
          setEstado({ tipo: 'error', error: e as ErrorApi });
          return;
        }
      }
      temporizador = setTimeout(() => void consultar(), INTERVALO_TAREA_MS);
    };
    void consultar();
    return () => {
      cancelado = true;
      clearTimeout(temporizador);
    };
  }, [tareaId, loteId]);

  const armarPlan = useCallback(() => {
    if (!loteId) return;
    setArmando(true);
    setErrorArmar(null);
    generarPlan(loteId)
      .then(({ tarea_id }) => setEstado({ tipo: 'calculando', tareaId: tarea_id, tarea: null }))
      .catch((e: ErrorApi) => {
        if (e.codigo === 'DIAGNOSTICO_NO_DISPONIBLE') setEstado({ tipo: 'sin_diagnostico' });
        else setErrorArmar(e.mensaje);
      })
      .finally(() => setArmando(false));
  }, [loteId]);

  const planCalculado = estado.tipo === 'calculando' ? estado.tarea?.plan_id ?? null : null;
  const verPlanCalculado = useCallback(() => {
    if (!planCalculado || !loteId) return;
    setEstado({ tipo: 'cargando' });
    Promise.all([obtenerPlan(planCalculado), obtenerLluviasEsperadas(loteId).catch(() => null)])
      .then(([plan, lluvias]) => {
        guardarPlan(loteId, { plan, lluvias });
        setEstado({ tipo: 'listo', plan, lluvias, desdeGuardado: false });
      })
      .catch((e: ErrorApi) => setEstado({ tipo: 'error', error: e }));
  }, [planCalculado, loteId]);

  const reintentar = useCallback(() => setIntento((n) => n + 1), []);

  // Cuando vuelve la conexión (y solo en ese momento), si se mostraba la copia guardada o un error de
  // red, se recarga. Solo en la transición: si el servidor sigue sin responder no se reintenta en bucle.
  const recargarAlVolver =
    (estado.tipo === 'listo' && estado.desdeGuardado) || (estado.tipo === 'error' && estado.error.codigo === 'RED_SIN_CONEXION');
  const estabaSinConexion = useRef(sinConexion);
  useEffect(() => {
    const volvio = estabaSinConexion.current && !sinConexion;
    estabaSinConexion.current = sinConexion;
    if (volvio && recargarAlVolver) setIntento((n) => n + 1);
  }, [sinConexion, recargarAlVolver]);

  return { lotes, loteId, estado, sinConexion, armando, errorArmar, reintentar, armarPlan, verPlanCalculado };
}
