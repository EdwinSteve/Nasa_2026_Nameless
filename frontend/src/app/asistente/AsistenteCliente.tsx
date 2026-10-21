"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { AsistenteView } from "@/routes/AsistenteView";

// Envoltorio cliente: la página del servidor no puede pasar funciones como props.
export function AsistenteCliente(props: { lotePedido: string | null; cultivoId: string | null; planId: string | null }) {
  const router = useRouter();
  const consulta = useSearchParams();
  return (
    <AsistenteView
      {...props}
      onCambiarLote={(id) => {
        // Al cambiar de lote se conserva el cultivo y el plan de donde venía
        const nueva = new URLSearchParams(consulta.toString());
        nueva.set("lote", id);
        router.replace(`/asistente?${nueva.toString()}`);
      }}
    />
  );
}
