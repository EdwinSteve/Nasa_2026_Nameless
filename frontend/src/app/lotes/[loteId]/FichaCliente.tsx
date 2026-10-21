"use client";

import { useRouter } from "next/navigation";
import { FichaLoteView } from "@/routes/FichaLoteView";

export function FichaCliente({ loteId }: { loteId: string }) {
  const router = useRouter();
  return <FichaLoteView loteId={loteId} onIngresar={() => router.push("/ingresar")} />;
}
