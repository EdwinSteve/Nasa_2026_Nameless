import { DiagnosticoCliente } from "./DiagnosticoCliente";
import { FichaCliente } from "./FichaCliente";

// /lotes/:id?tarea=X → diagnóstico en curso
// /lotes/:id         → ficha del lote (provisional) con la recomendación de cultivos
export default async function LotePage({
  params,
  searchParams,
}: {
  params: Promise<{ loteId: string }>;
  searchParams: Promise<{ tarea?: string }>;
}) {
  const { loteId } = await params;
  const { tarea } = await searchParams;

  if (tarea) {
    return <DiagnosticoCliente loteId={loteId} tareaId={tarea} />;
  }

  return <FichaCliente loteId={loteId} />;
}
