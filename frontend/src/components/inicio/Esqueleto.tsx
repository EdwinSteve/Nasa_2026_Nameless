// Bloque gris animado mientras llegan los datos.
export function Esqueleto({ className = '' }: { className?: string }) {
  return <div aria-hidden="true" className={`animate-pulse rounded-3xl bg-[#E8E1D3] motion-reduce:animate-none ${className}`} />;
}

/** La forma de la pantalla Inicio mientras carga: mismo orden y columnas que la real. */
export function EsqueletoInicio() {
  return (
    <div role="status" className="flex flex-col gap-5">
      <span className="sr-only">Cargando su inicio…</span>
      <Esqueleto className="h-24 w-full max-w-md" />
      <div className="flex flex-col gap-5 lg:grid lg:grid-cols-12">
        <Esqueleto className="h-[28rem] lg:col-span-7" />
        <div className="flex flex-col gap-5 lg:col-span-5">
          <Esqueleto className="h-56" />
          <Esqueleto className="h-64" />
        </div>
      </div>
    </div>
  );
}
