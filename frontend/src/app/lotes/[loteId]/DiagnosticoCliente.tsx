"use client";

import { useRouter } from "next/navigation";
import { DiagnosticoLoteView } from "@/routes/DiagnosticoLoteView";

// Envoltorio cliente: la página del servidor no puede pasar funciones como props.
export function DiagnosticoCliente({ loteId, tareaId }: { loteId: string; tareaId: string }) {
  const router = useRouter();
  return (
    <DiagnosticoLoteView
      loteId={loteId}
      tareaId={tareaId}
      onNavigateFicha={(id) => router.replace(`/lotes/${id}`)}
    />
  );
}
