// "¿Cuándo sembrar?": cuántos años de cada 10 le va bien según la fecha de siembra, en SVG propio.
// La mejor época va como franja verde. El punto elegido funciona como un control deslizante:
// se toca o se arrastra sobre la gráfica, y con el teclado se mueve con las flechas.
'use client';

import { useId, useState, type KeyboardEvent, type PointerEvent } from 'react';
import type { VentanaSiembra } from '../../api/tipos';
import { formatearDiaMes, formatearMesCorto } from '../../lib/fechas';
import { textoMejorEpoca, textoSiSiembra } from '../../lib/plan';

const ANCHO = 600;
const ALTO = 200;
const yDe = (f: number) => ALTO - (Math.max(0, Math.min(10, f)) / 10) * ALTO;

interface Props {
  ventana: VentanaSiembra;
  nombreCultivo: string;
}

export function GraficaVentanaSiembra({ ventana, nombreCultivo }: Props) {
  const idTitulo = useId();
  const idResumen = useId();
  const { puntos } = ventana;
  const n = puntos.length;
  const iInicio = Math.max(0, puntos.findIndex((p) => p.fecha >= ventana.mejor_inicio));
  const iFinEncontrado = puntos.findIndex((p) => p.fecha > ventana.mejor_fin);
  const iFin = (iFinEncontrado === -1 ? n : iFinEncontrado) - 1;
  const [elegido, setElegido] = useState(() => Math.round((iInicio + Math.max(iInicio, iFin)) / 2));

  if (n < 2) return null;

  const xDe = (i: number) => (i / (n - 1)) * ANCHO;
  const pct = (i: number) => (i / (n - 1)) * 100;
  const paso = ANCHO / (n - 1);
  const linea = puntos.map((p, i) => `${xDe(i).toFixed(1)},${yDe(p.frecuencia_exito).toFixed(1)}`).join(' ');
  const area = `0,${ALTO} ${linea} ${ANCHO},${ALTO}`;
  const franjaX = Math.max(0, xDe(iInicio) - paso / 2);
  const franjaAncho = Math.min(ANCHO, xDe(Math.max(iInicio, iFin)) + paso / 2) - franjaX;

  const maximo = Math.max(...puntos.map((p) => p.frecuencia_exito));
  const minimo = Math.min(...puntos.map((p) => p.frecuencia_exito));
  const epoca = textoMejorEpoca(ventana.mejor_inicio, ventana.mejor_fin);
  const resumen = `${epoca.replace('Mejor época: ', `La mejor época para sembrar ${nombreCultivo.toLowerCase()} es `)}: ${maximo} de cada 10 años le va bien. Fuera de esa época baja hasta ${minimo} de cada 10.`;

  // La primera semana de cada mes lleva la etiqueta del mes en el eje
  const marcasMes = puntos
    .map((p, i) => ({ i, mes: p.fecha.slice(0, 7) }))
    .filter((m, k, todas) => k === 0 || m.mes !== todas[k - 1].mes)
    // Si el primer mes casi no alcanza a verse, su etiqueta se encimaría con la del siguiente
    .filter((m, k, marcas) => k + 1 >= marcas.length || marcas[k + 1].i - m.i >= 3);

  const punto = puntos[Math.min(elegido, n - 1)];
  const valorTexto = textoSiSiembra(punto.fecha, punto.frecuencia_exito);

  const elegirDesdePuntero = (e: PointerEvent<HTMLDivElement>) => {
    const caja = e.currentTarget.getBoundingClientRect();
    const fraccion = (e.clientX - caja.left) / caja.width;
    setElegido(Math.max(0, Math.min(n - 1, Math.round(fraccion * (n - 1)))));
  };

  const alTeclado = (e: KeyboardEvent<HTMLDivElement>) => {
    const nuevo =
      e.key === 'ArrowRight' || e.key === 'ArrowUp'
        ? elegido + 1
        : e.key === 'ArrowLeft' || e.key === 'ArrowDown'
          ? elegido - 1
          : e.key === 'PageUp'
            ? elegido + 4
            : e.key === 'PageDown'
              ? elegido - 4
              : e.key === 'Home'
                ? 0
                : e.key === 'End'
                  ? n - 1
                  : null;
    if (nuevo === null) return;
    e.preventDefault();
    setElegido(Math.max(0, Math.min(n - 1, nuevo)));
  };

  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-4 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 id={idTitulo} className="font-titulo text-xl font-extrabold text-tinta">
            ¿Cuándo sembrar?
          </h2>
          <p className="text-sm text-tinta/75">Años de cada 10 en que le va bien, según la fecha de siembra</p>
        </div>
        <span className="rounded-full bg-hoja/25 px-3 py-1 text-sm font-bold text-campo">{epoca}</span>
      </div>

      <div className="rounded-2xl bg-crema p-3">
        <div className="grid grid-cols-[auto_1fr] gap-2">
          <div aria-hidden="true" className="flex h-48 flex-col justify-between text-right text-sm font-semibold text-tinta/60">
            <span>10</span>
            <span>5</span>
            <span>0</span>
          </div>
          <div
            role="slider"
            tabIndex={0}
            aria-label="Fecha de siembra"
            aria-valuemin={0}
            aria-valuemax={n - 1}
            aria-valuenow={elegido}
            aria-valuetext={valorTexto}
            aria-describedby={idResumen}
            onKeyDown={alTeclado}
            onPointerDown={(e) => {
              e.currentTarget.setPointerCapture(e.pointerId);
              elegirDesdePuntero(e);
            }}
            onPointerMove={(e) => {
              if (e.buttons > 0) elegirDesdePuntero(e);
            }}
            className="relative h-48 cursor-pointer touch-none rounded-lg outline-none focus-visible:ring-4 focus-visible:ring-agua/50"
          >
            <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden="true">
              <title>Frecuencia de éxito según la fecha de siembra</title>
              <rect x={franjaX} y={0} width={franjaAncho} height={ALTO} className="fill-hoja/30" />
              <line x1={0} x2={ANCHO} y1={ALTO / 2} y2={ALTO / 2} className="stroke-tinta/10" strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />

              <polygon points={area} className="fill-campo/10" />
              <polyline points={linea} fill="none" className="stroke-campo" strokeWidth={3} strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
              <line x1={xDe(elegido)} x2={xDe(elegido)} y1={0} y2={ALTO} className="stroke-sol" strokeWidth={2} vectorEffect="non-scaling-stroke" />
            </svg>
            <span
              aria-hidden="true"
              className="pointer-events-none absolute h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-white bg-sol shadow"
              style={{ left: `${pct(elegido)}%`, top: `${(yDe(punto.frecuencia_exito) / ALTO) * 100}%` }}
            />
          </div>
          <span />
          <div aria-hidden="true" className="relative h-6 text-sm font-semibold text-tinta/70">
            {marcasMes.map((m) => (
              <span
                key={m.mes}
                className="absolute -translate-x-1/2 whitespace-nowrap first:translate-x-0"
                style={{ left: `${pct(m.i)}%` }}
              >
                {formatearMesCorto(m.mes)}
              </span>
            ))}
          </div>
        </div>
      </div>

      <p aria-hidden="true" className="rounded-2xl border-2 border-sol/40 bg-sol/10 p-4 text-lg font-bold text-tinta">
        {valorTexto}
      </p>
      <p className="text-sm text-tinta/70">Toque la gráfica o use las flechas del teclado para ver otra fecha.</p>
      <p id={idResumen} className="text-base text-tinta">
        {resumen}
      </p>
      <ul className="sr-only">
        {puntos.map((p) => (
          <li key={p.fecha}>
            {formatearDiaMes(p.fecha)}: {p.frecuencia_exito} de cada 10 años
          </li>
        ))}
      </ul>
    </section>
  );
}
