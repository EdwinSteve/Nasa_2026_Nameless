// src/routes/DiagnosticoLoteView.tsx
'use client';

import React, { useEffect, useState } from 'react';
import { TaskProgress } from '../components/feedback/TaskProgress';
import { ErrorCard } from '../components/feedback/ErrorCard';
import type { TareaDiagnosticoResponse } from '../api/tipos';
import { obtenerTareaDiagnostico } from '../api/services';

const INTERVALO_CONSULTA_MS = 2000;
const MAX_FALLOS_SEGUIDOS = 3;

export interface DiagnosticoLoteViewProps {
  loteId: string;
  tareaId: string;
  onNavigateFicha?: (loteId: string) => void;
}

export const DiagnosticoLoteView: React.FC<DiagnosticoLoteViewProps> = ({
  loteId,
  tareaId,
  onNavigateFicha = (id) => console.log('[Router Navigation] ->', `/lotes/${id}`)
}) => {
  const [tarea, setTarea] = useState<TareaDiagnosticoResponse | null>(null);
  const [errorConsulta, setErrorConsulta] = useState<string | null>(null);
  // Cambiarlo reinicia el ciclo de consultas (botón "Reintentar")
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let cancelado = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let fallosSeguidos = 0;

    const consultar = async () => {
      try {
        const respuesta = await obtenerTareaDiagnostico(loteId, tareaId);
        if (cancelado) return;
        fallosSeguidos = 0;
        setTarea(respuesta);
        if (respuesta.estado === 'lista' || respuesta.estado === 'fallida') return;
      } catch (err: unknown) {
        if (cancelado) return;
        console.error('Error consultando el diagnóstico:', err);
        fallosSeguidos += 1;
        if (fallosSeguidos >= MAX_FALLOS_SEGUIDOS) {
          setErrorConsulta('Perdimos la conexión mientras analizábamos su lote.');
          return;
        }
      }
      timer = setTimeout(() => void consultar(), INTERVALO_CONSULTA_MS);
    };

    void consultar();

    return () => {
      cancelado = true;
      clearTimeout(timer);
    };
  }, [loteId, tareaId, intento]);

  const reintentar = () => {
    setErrorConsulta(null);
    setIntento((n) => n + 1);
  };

  return (
    <main className="min-h-screen bg-[#F7F3EA] text-[#14202B]">
      {errorConsulta && (
        <div className="max-w-[560px] mx-auto px-4 pt-4">
          <ErrorCard mensaje={errorConsulta} onRetry={reintentar} retryLabel="Volver a intentar" />
        </div>
      )}

      {tarea ? (
        <TaskProgress
          tarea={tarea}
          onCompletado={() => onNavigateFicha(loteId)}
          onReintentar={reintentar}
        />
      ) : (
        !errorConsulta && (
          <p role="status" className="max-w-[560px] mx-auto px-4 py-10 text-base font-semibold text-[#14202B]/70">
            Conectando con los satélites...
          </p>
        )
      )}
    </main>
  );
};
