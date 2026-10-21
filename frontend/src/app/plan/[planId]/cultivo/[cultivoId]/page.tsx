import { DetalleCultivoView } from "@/routes/DetalleCultivoView";

// /plan/:planId/cultivo/:cultivoId?rotacion=R&lote=L → detalle de un cultivo del plan
export default async function DetalleCultivoPage({
  params,
  searchParams,
}: {
  params: Promise<{ planId: string; cultivoId: string }>;
  searchParams: Promise<{ rotacion?: string; lote?: string }>;
}) {
  const { planId, cultivoId } = await params;
  const { rotacion, lote } = await searchParams;
  return (
    <DetalleCultivoView
      planId={decodeURIComponent(planId)}
      cultivoId={decodeURIComponent(cultivoId)}
      rotacionId={rotacion ?? null}
      loteId={lote ?? null}
    />
  );
}
