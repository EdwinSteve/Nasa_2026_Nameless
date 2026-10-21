// src/hooks/useDetalleCultivo.ts
// Datos del detalle de un cultivo dentro de un plan: el plan y la ventana de siembra.
'use client';

import { useCallback, useEffect, useState } from 'react';
import type { ErrorApi, Plan, VentanaSiembra } from '../api/tipos';
import { obtenerPlan, obtenerVentanaSiembra } from '../api/services';
import { buscarPlanGuardado } from '../lib/planGuardado';
import { useSinConexion } from './useResumenInicio';

export type EstadoDetalle =
  | { tipo: 'cargando' }
  /** Sin conexión, con el plan guardado pero sin la ventana: se muestra lo que hay. */
  | { tipo: 'listo'; plan: Plan; ventana: VentanaSiembra | null }
  | { tipo: 'error'; error: ErrorApi };

export function useDetalleCultivo(planId: string, cultivoId: string) {
  const [estado, setEstado] = useState<EstadoDetalle>({ tipo: 'cargando' });
  const [intento, setIntento] = useState(0);
  const sinConexion = useSinConexion();

  useEffect(() => {
    let cancelado = false;
    setEstado({ tipo: 'cargando' });
    Promise.all([obtenerPlan(planId), obtenerVentanaSiembra(planId, cultivoId)])
      .then(([plan, ventana]) => {
        if (!cancelado) setEstado({ tipo: 'listo', plan, ventana });
      })
      .catch((e: ErrorApi) => {
        if (cancelado) return;
        const guardado = e.codigo === 'RED_SIN_CONEXION' ? buscarPlanGuardado(planId) : null;
        setEstado(guardado ? { tipo: 'listo', plan: guardado, ventana: null } : { tipo: 'error', error: e });
      });
    return () => {
      cancelado = true;
    };
  }, [planId, cultivoId, intento]);

  const reintentar = useCallback(() => setIntento((n) => n + 1), []);
  return { estado, sinConexion, reintentar };
}
