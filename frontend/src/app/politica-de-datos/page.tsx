"use client";

import { useEffect, useState } from "react";
import { obtenerPoliticaVigente } from "@/api/services";
import type { PoliticaVigente } from "@/api/tipos";
import { ErrorCard } from "@/components/feedback/ErrorCard";

// Texto completo de la política que el productor acepta en el paso 1 del registro.
export default function PoliticaDeDatosPage() {
  const [politica, setPolitica] = useState<PoliticaVigente | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let cancelado = false;
    obtenerPoliticaVigente()
      .then((p) => !cancelado && setPolitica(p))
      .catch(() => !cancelado && setError("No pudimos cargar la política de datos."));
    return () => {
      cancelado = true;
    };
  }, [intento]);

  return (
    <main className="min-h-screen bg-[#F7F3EA] text-[#14202B]">
      <article className="max-w-xl mx-auto px-4 py-8 flex flex-col gap-4">
        <h1 className="text-3xl font-black text-[#1F4D2B]">Política de tratamiento de datos</h1>
        {error && (
          <ErrorCard
            mensaje={error}
            onRetry={() => {
              setError(null);
              setIntento((n) => n + 1);
            }}
          />
        )}
        {politica ? (
          <>
            <p className="text-sm font-bold text-[#14202B]/60">Versión {politica.version}</p>
            <div className="text-base leading-relaxed whitespace-pre-line">{politica.contenido}</div>
          </>
        ) : (
          !error && <p role="status" className="text-base text-[#14202B]/70">Cargando...</p>
        )}
      </article>
    </main>
  );
}
