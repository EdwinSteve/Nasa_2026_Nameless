export interface IndicadorCarruselProps {
  total: number;
  activo: number;
  onSeleccionar: (indice: number) => void;
}

export function IndicadorCarrusel({ total, activo, onSeleccionar }: IndicadorCarruselProps) {
  return (
    <div className="flex items-center justify-center">
      {Array.from({ length: total }, (_, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onSeleccionar(i)}
          aria-label={`Ir a la diapositiva ${i + 1} de ${total}`}
          aria-current={i === activo ? 'true' : undefined}
          className="flex h-11 w-11 items-center justify-center rounded-full"
        >
          <span
            aria-hidden="true"
            className={`block h-2.5 rounded-full transition-all duration-300 motion-reduce:transition-none ${i === activo ? 'w-8 bg-campo' : 'w-2.5 bg-borde'}`}
          />
        </button>
      ))}
    </div>
  );
}
