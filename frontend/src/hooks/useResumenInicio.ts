// src/hooks/useResumenInicio.ts
// Datos de la pantalla Inicio: carga, error, reintento y estado de la conexión.
'use client';

import { useCallback, useEffect, useState, useSyncExternalStore } from 'react';
import type { ErrorApi, ResumenInicio } from '../api/tipos';
import { obtenerResumenInicio } from '../api/services';

export type EstadoCarga = 'cargando' | 'listo' | 'error';

/** Qué variantes de la pantalla corresponden a estos datos. */
export interface ClasificacionInicio {
  esNuevo: boolean;           // sin logros ni series todavía
  sinLote: boolean;           // no ha marcado ningún lote
  sinRecomendacion: boolean;  // hoy no hay nada especial que hacer
  puedeRegistrarRiego: boolean;
}

export function clasificarResumen(datos: ResumenInicio): ClasificacionInicio {
  const recomendacion = datos.recomendacion_hoy;
  return {
    esNuevo: datos.logros === null && datos.series === null,
    sinLote: datos.lote_principal === null,
    sinRecomendacion: recomendacion === null || recomendacion.tipo === 'ninguna',
    puedeRegistrarRiego: recomendacion?.tipo === 'riego' && datos.lote_principal !== null
  };
}

function suscribirConexion(avisar: () => void): () => void {
  window.addEventListener('online', avisar);
  window.addEventListener('offline', avisar);
  return () => {
    window.removeEventListener('online', avisar);
    window.removeEventListener('offline', avisar);
  };
}

/** true si el navegador dice que no hay red. En el servidor se asume que sí hay. */
export function useSinConexion(): boolean {
  return useSyncExternalStore(
    suscribirConexion,
    () => !navigator.onLine,
    () => false
  );
}

export interface UseResumenInicio {
  estado: EstadoCarga;
  datos: ResumenInicio | null;
  error: ErrorApi | null;
  sinConexion: boolean;
  reintentar: () => void;
}

export function useResumenInicio(): UseResumenInicio {
  const [estado, setEstado] = useState<EstadoCarga>('cargando');
  const [datos, setDatos] = useState<ResumenInicio | null>(null);
  const [error, setError] = useState<ErrorApi | null>(null);
  const [intento, setIntento] = useState(0);
  const sinConexion = useSinConexion();

  useEffect(() => {
    let cancelado = false;
    setEstado('cargando');
    setError(null);
    obtenerResumenInicio()
      .then((respuesta) => {
        if (cancelado) return;
        setDatos(respuesta);
        setEstado('listo');
      })
      .catch((e: ErrorApi) => {
        if (cancelado) return;
        setError(e);
        setEstado('error');
      });
    return () => {
      cancelado = true;
    };
  }, [intento]);

  // Al volver la conexión después de un error, se reintenta solo
  useEffect(() => {
    if (!sinConexion && estado === 'error' && error?.codigo === 'RED_SIN_CONEXION') {
      setIntento((n) => n + 1);
    }
  }, [sinConexion, estado, error]);

  const reintentar = useCallback(() => setIntento((n) => n + 1), []);

  return { estado, datos, error, sinConexion, reintentar };
}
