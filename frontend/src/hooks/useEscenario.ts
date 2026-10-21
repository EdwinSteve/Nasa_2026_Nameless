// src/hooks/useEscenario.ts
// "¿Y si el clima cambia?": pide la frecuencia de éxito con otra lluvia y otro calor.
// Espera 400 ms sin cambios antes de llamar y descarta respuestas de valores viejos.
'use client';

import { useEffect, useRef, useState } from 'react';
import type { ErrorApi } from '../api/tipos';
import { simularEscenario } from '../api/services';

export const ESPERA_ESCENARIO_MS = 400;

export interface UseEscenario {
  lluvia: number;
  temperatura: number;
  setLluvia: (valor: number) => void;
  setTemperatura: (valor: number) => void;
  /** Con el clima de siempre es la frecuencia base; si no, la que devolvió el servicio. */
  frecuencia: number | null;
  calculando: boolean;
  error: string | null;
}

export function useEscenario(planId: string, cultivoId: string, base: number | null): UseEscenario {
  const [lluvia, setLluvia] = useState(0);
  const [temperatura, setTemperatura] = useState(0);
  const [simulada, setSimulada] = useState<number | null>(null);
  const [calculando, setCalculando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ultimaPeticion = useRef(0);

  const climaDeSiempre = lluvia === 0 && temperatura === 0;

  useEffect(() => {
    if (climaDeSiempre) {
      ultimaPeticion.current++;
      setSimulada(null);
      setCalculando(false);
      setError(null);
      return;
    }
    setCalculando(true);
    const temporizador = setTimeout(() => {
      const numero = ++ultimaPeticion.current;
      simularEscenario(planId, cultivoId, lluvia, temperatura)
        .then(({ frecuencia_exito }) => {
          if (numero !== ultimaPeticion.current) return;
          setSimulada(frecuencia_exito);
          setError(null);
        })
        .catch((e: ErrorApi) => {
          if (numero === ultimaPeticion.current) setError(e.mensaje);
        })
        .finally(() => {
          if (numero === ultimaPeticion.current) setCalculando(false);
        });
    }, ESPERA_ESCENARIO_MS);
    return () => clearTimeout(temporizador);
  }, [planId, cultivoId, lluvia, temperatura, climaDeSiempre]);

  return {
    lluvia,
    temperatura,
    setLluvia,
    setTemperatura,
    frecuencia: climaDeSiempre ? base : simulada,
    calculando,
    error
  };
}
