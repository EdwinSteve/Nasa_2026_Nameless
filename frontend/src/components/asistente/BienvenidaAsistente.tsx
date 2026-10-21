// La primera vez: saludo y preguntas sugeridas grandes.
import { AvatarAsistente } from './AvatarAsistente';

interface Props {
  nombre: string | null;
  preguntas: string[];
  onPreguntar: (pregunta: string) => void;
  desactivado: boolean;
}

export function BienvenidaAsistente({ nombre, preguntas, onPreguntar, desactivado }: Props) {
  return (
    <section aria-labelledby="saludo-asistente" className="flex flex-col gap-4 py-2">
      <div className="flex items-center gap-3">
        <AvatarAsistente tamano="grande" />
        <h2 id="saludo-asistente" className="font-titulo text-2xl font-extrabold leading-tight text-tinta">
          Hola{nombre ? `, ${nombre}` : ''}. Pregúnteme sobre su lote
        </h2>
      </div>
      <p className="text-base text-tinta/80">Puede escribir o hablar. Estas son algunas preguntas que puede hacerme:</p>
      <PreguntasSugeridas preguntas={preguntas} onPreguntar={onPreguntar} desactivado={desactivado} />
    </section>
  );
}

export function PreguntasSugeridas({ preguntas, onPreguntar, desactivado }: Omit<Props, 'nombre'>) {
  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {preguntas.map((p) => (
        <li key={p}>
          <button
            type="button"
            onClick={() => onPreguntar(p)}
            disabled={desactivado}
            className="flex min-h-16 w-full items-center rounded-2xl border-2 border-campo/20 bg-white px-4 text-left text-lg font-bold text-campo shadow-sm hover:border-campo/50 disabled:opacity-60"
          >
            {p}
          </button>
        </li>
      ))}
    </ul>
  );
}
