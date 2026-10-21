// Barras de una onda de voz: en vivo mientras se graba, o decorativa en una nota ya enviada.
export function OndaVoz({ niveles, clase = 'bg-current' }: { niveles: number[]; clase?: string }) {
  return (
    <span aria-hidden="true" className="flex h-8 flex-1 items-center gap-[3px]">
      {niveles.map((n, i) => (
        <span key={i} className={`w-1 shrink-0 rounded-full ${clase}`} style={{ height: `${Math.max(12, Math.round(n * 100))}%` }} />
      ))}
    </span>
  );
}
