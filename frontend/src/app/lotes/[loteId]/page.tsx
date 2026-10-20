import { DiagnosticoCliente } from "./DiagnosticoCliente";

// /lotes/:id?tarea=X → diagnóstico en curso
// /lotes/:id         → ficha del lote (pendiente de diseño)
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

  return (
    <main className="min-h-screen max-w-xl mx-auto p-6 flex flex-col justify-center gap-3">
      <h1 className="text-3xl font-black text-[#1F4D2B]">Ficha del lote</h1>
      <p className="text-base text-[#14202B]/80">Esta pantalla está pendiente de diseño en Stitch.</p>
      <p className="text-sm font-mono text-[#14202B]/60">Lote: {loteId}</p>
    </main>
  );
}
