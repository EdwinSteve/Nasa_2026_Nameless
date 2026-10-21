import { AsistenteCliente } from "./AsistenteCliente";

// /asistente?lote=L&cultivo=C&plan=P → chat con el Asistente SURCO sobre el lote L.
// cultivo y plan llegan desde el detalle de un cultivo del Plan de siembra.
export default async function AsistentePage({
  searchParams,
}: {
  searchParams: Promise<{ lote?: string; cultivo?: string; plan?: string }>;
}) {
  const { lote, cultivo, plan } = await searchParams;
  return <AsistenteCliente lotePedido={lote ?? null} cultivoId={cultivo ?? null} planId={plan ?? null} />;
}
