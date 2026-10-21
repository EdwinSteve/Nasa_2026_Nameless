// Línea de las cinco etapas del cultivo, con la actual marcada.
import type { EtapaCultivo, ResumenInicio } from '../../api/tipos';
import { formatearDiaMes } from '../../lib/fechas';
import { IconoCheck } from '../iconos/Iconos';

const ETAPAS: { codigo: EtapaCultivo; nombre: string }[] = [
  { codigo: 'siembra', nombre: 'Siembra' },
  { codigo: 'crecimiento', nombre: 'Crecimiento' },
  { codigo: 'floracion', nombre: 'Floración' },
  { codigo: 'llenado', nombre: 'Llenado' },
  { codigo: 'cosecha', nombre: 'Cosecha' }
];

type Cultivo = NonNullable<NonNullable<ResumenInicio['lote_principal']>['cultivo']>;

export function EtapasCultivo({ cultivo }: { cultivo: Cultivo }) {
  const actual = ETAPAS.findIndex((e) => e.codigo === cultivo.etapa_actual);
  return (
    <div className="flex flex-col gap-3">
      <h3 className="font-titulo text-lg font-extrabold text-tinta">Etapa del cultivo: {cultivo.nombre}</h3>
      <ol className="grid grid-cols-5 gap-1.5" aria-label="Etapas del cultivo">
        {ETAPAS.map((etapa, i) => {
          const hecha = i < actual;
          const esActual = i === actual;
          return (
            <li key={etapa.codigo} aria-current={esActual ? 'step' : undefined} className="flex flex-col items-center gap-1.5 text-center">
              <span
                className={`h-2.5 w-full rounded-full ${hecha ? 'bg-campo' : esActual ? 'bg-sol' : 'bg-[#E8E1D3]'}`}
                aria-hidden="true"
              />
              <span className={`flex h-9 w-9 items-center justify-center rounded-full ${hecha ? 'bg-hoja/25 text-campo' : esActual ? 'bg-sol text-white' : 'bg-[#E8E1D3] text-tinta/50'}`}>
                {hecha ? <IconoCheck tamano={20} /> : <span className="text-sm font-black">{i + 1}</span>}
              </span>
              <span className={`w-full hyphens-auto break-words text-sm leading-tight ${esActual ? 'font-extrabold text-tinta' : 'font-semibold text-tinta/70'}`}>
                {etapa.nombre}
              </span>
              {esActual && <span className="rounded-full bg-sol/15 px-2 text-sm font-bold text-[#9A4A12]">Hoy</span>}
            </li>
          );
        })}
      </ol>
      <div className="grid grid-cols-2 gap-2 rounded-2xl bg-crema p-3 text-base">
        <p>
          <span className="font-bold">Día {cultivo.dia_actual}</span> de {cultivo.dias_ciclo}
        </p>
        <p>
          Cosecha estimada: <span className="font-bold">{formatearDiaMes(cultivo.fecha_cosecha_estimada)}</span>
        </p>
      </div>
    </div>
  );
}
