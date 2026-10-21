"use client";

import { useRouter } from "next/navigation";
import { PlanView } from "@/routes/PlanView";

// Envoltorio cliente: la página del servidor no puede pasar funciones como props.
export function PlanCliente({ lotePedido }: { lotePedido: string | null }) {
  const router = useRouter();
  return (
    <PlanView
      lotePedido={lotePedido}
      onCambiarLote={(id) => router.replace(`/plan?lote=${encodeURIComponent(id)}`)}
      onNavigate={(ruta) => router.push(ruta)}
    />
  );
}
