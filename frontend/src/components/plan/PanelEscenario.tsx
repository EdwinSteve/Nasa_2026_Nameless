// "¿Y si el clima cambia?": dos controles deslizantes y la tarjeta de frecuencia que se actualiza.
'use client';

import { useId, type ReactNode } from 'react';
import { useEscenario } from '../../hooks/useEscenario';
import { LLUVIA, TEMPERATURA, textoLluvia, textoTemperatura } from '../../lib/plan';
import { IconoGota, IconoTermometro } from '../iconos/Iconos';

interface ControlProps {
  etiqueta: string;
  icono: ReactNode;
  valor: number;
  min: number;
  max: number;
  paso: number;
  extremos: [string, string];
  texto: (valor: number) => string;
  onCambiar: (valor: number) => void;
}

function Control({ etiqueta, icono, valor, min, max, paso, extremos, texto, onCambiar }: ControlProps) {
  const id = useId();
  return (
    <div className="flex flex-col gap-2 rounded-2xl bg-crema p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <label htmlFor={id} className="flex items-center gap-2 text-base font-bold text-tinta">
          {icono}
          {etiqueta}
        </label>
        <span aria-hidden="true" className="text-base font-semibold text-campo">
          {texto(valor)}
        </span>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={paso}
        value={valor}
        aria-valuetext={texto(valor)}
        onChange={(e) => onCambiar(Number(e.target.value))}
        className="h-11 w-full cursor-pointer accent-[#1f4d2b]"
      />
      <div aria-hidden="true" className="flex justify-between text-sm font-semibold text-tinta/70">
        <span>{extremos[0]}</span>
        <span>{extremos[1]}</span>
      </div>
    </div>
  );
}

interface Props {
  planId: string;
  cultivoId: string;
  nombreCultivo: string;
  /** Frecuencia con el clima de siempre (la de la mejor época). */
  base: number | null;
  /** Sin conexión el servicio no responde: los controles se desactivan. */
  desactivado: boolean;
}

export function PanelEscenario({ planId, cultivoId, nombreCultivo, base, desactivado }: Props) {
  const idTitulo = useId();
  const { lluvia, temperatura, setLluvia, setTemperatura, frecuencia, calculando, error } = useEscenario(planId, cultivoId, base);
  const climaDeSiempre = lluvia === 0 && temperatura === 0;
  const condicion = [lluvia !== 0 ? textoLluvia(lluvia) : null, temperatura !== 0 ? textoTemperatura(temperatura) : null]
    .filter(Boolean)
    .join(' y ')
    .toLowerCase();

  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-4 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <div>
        <h2 id={idTitulo} className="font-titulo text-xl font-extrabold text-tinta">
          ¿Y si el clima cambia?
        </h2>
        <p className="text-sm text-tinta/75">Mueva los controles para ver qué pasaría con su {nombreCultivo.toLowerCase()}.</p>
      </div>

      <fieldset disabled={desactivado} className="flex flex-col gap-3 disabled:opacity-60">
        <legend className="sr-only">Cambios en el clima</legend>
        <Control
          etiqueta="Lluvia"
          icono={<IconoGota tamano={22} className="text-agua" />}
          valor={lluvia}
          min={LLUVIA.min}
          max={LLUVIA.max}
          paso={LLUVIA.paso}
          extremos={['Menos lluvia', 'Más lluvia']}
          texto={textoLluvia}
          onCambiar={setLluvia}
        />
        <Control
          etiqueta="Temperatura"
          icono={<IconoTermometro tamano={22} className="text-sol" />}
          valor={temperatura}
          min={TEMPERATURA.min}
          max={TEMPERATURA.max}
          paso={TEMPERATURA.paso}
          extremos={['Como siempre', 'Más calor']}
          texto={textoTemperatura}
          onCambiar={setTemperatura}
        />
      </fieldset>

      <div aria-live="polite" className="rounded-2xl border-2 border-campo/30 bg-hoja/10 p-4">
        <p className="text-sm font-semibold text-tinta/75">
          {climaDeSiempre ? 'Con el clima de siempre, en la mejor época' : `Con ${condicion}`}
        </p>
        {calculando ? (
          <p className="font-titulo text-2xl font-extrabold text-tinta/60">Calculando…</p>
        ) : frecuencia !== null ? (
          <p className="font-titulo text-2xl font-extrabold text-campo">{frecuencia} de cada 10 años le va bien</p>
        ) : null}
        {!calculando && !climaDeSiempre && base !== null && frecuencia !== null && frecuencia !== base && (
          <p className="text-base text-tinta">
            {frecuencia < base ? `Son ${base - frecuencia} años menos de cada 10 que con el clima de siempre.` : `Son ${frecuencia - base} años más de cada 10 que con el clima de siempre.`}
          </p>
        )}
        {error && (
          <p role="alert" className="text-base font-semibold text-[#B23B3B]">
            No pudimos calcular este caso: {error}
          </p>
        )}
        {desactivado && <p className="text-base text-tinta/80">Sin conexión no podemos calcular otros climas.</p>}
      </div>
    </section>
  );
}
