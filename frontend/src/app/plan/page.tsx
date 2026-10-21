import { PlanCliente } from "./PlanCliente";

// /plan?lote=X → plan de siembra del lote X (si no viene, el primero del usuario)
export default async function PlanPage({ searchParams }: { searchParams: Promise<{ lote?: string }> }) {
  const { lote } = await searchParams;
  return <PlanCliente lotePedido={lote ?? null} />;
}
