// src/components/feedback/TaskProgress.tsx
// Presentación del diagnóstico en curso. No consulta la API: recibe la tarea por props.
import React, { useCallback, useEffect, useRef } from 'react';
import { SatelliteScan } from './SatelliteScan';
import type { CodigoPasoTarea, PasoTarea, TareaDiagnosticoResponse } from '../../api/tipos';
import { formatearHectareas } from '../../lib/formato';

export interface TaskProgressProps {
  tarea: TareaDiagnosticoResponse;
  /** Se llama una sola vez: al tocar "Ver mi lote" o tras la espera automática. */
  onCompletado?: () => void;
  tiempoEsperaMs?: number;
  onSegundoPlano?: () => void;
  onReintentar?: () => void;
}

const limitar = (valor: number) => Math.min(100, Math.max(0, valor));

const Spinner: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg className={`${className} animate-spin`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
  </svg>
);

const ICONO_PASO: Record<CodigoPasoTarea, React.ReactNode> = {
  clima: (
    <>
      <circle cx="12" cy="12" r="5" strokeWidth="2.5" />
      <path strokeLinecap="round" strokeWidth="2.5" d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M6.34 17.66l-1.41 1.41m14.14-14.14l-1.41 1.41" />
    </>
  ),
  humedad: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 2.69l5.66 5.66a8 8 0 11-11.31 0z" />,
  suelo: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M2 17l10 5 10-5M2 12l10 5 10-5M12 2L2 7l10 5 10-5L12 2z" />,
  verdor: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M11 20A7 7 0 014 13C4 6 11 3 20 3C20 12 17 19 11 20ZM11 20L15 15" />
};

const ESTILO_TARJETA: Record<PasoTarea['estado'], string> = {
  lista: 'border-[#B8DEC0] bg-white shadow-sm',
  en_proceso: 'border-[#1F4D2B] bg-[#F7F3EA] shadow-md ring-1 ring-[#1F4D2B]/20',
  fallida: 'border-[#E8833A] bg-[#FFF8F2]',
  pendiente: 'border-[#D2C8B5]/60 bg-white opacity-80'
};

const ESTILO_ICONO: Record<PasoTarea['estado'], string> = {
  lista: 'bg-[#98E49E] text-[#14421E]',
  en_proceso: 'bg-[#1F4D2B] text-white shadow-sm',
  fallida: 'bg-[#E8833A] text-white',
  pendiente: 'bg-[#EDE7DA] text-[#14202B]/40'
};

const IconoEstadoPaso: React.FC<{ paso: PasoTarea }> = ({ paso }) => {
  if (paso.estado === 'lista') {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
      </svg>
    );
  }
  if (paso.estado === 'en_proceso') return <Spinner className="w-4 h-4" />;
  if (paso.estado === 'fallida') return <span className="text-base font-black" aria-hidden="true">!</span>;
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      {ICONO_PASO[paso.codigo]}
    </svg>
  );
};

const TarjetaPaso: React.FC<{ paso: PasoTarea }> = ({ paso }) => {
  const progreso = limitar(paso.progreso);
  const etiquetaProgreso = paso.estado === 'fallida' ? 'Falló' : `${progreso}%`;

  return (
    <li className={`p-4 rounded-2xl border-2 transition-all flex items-start gap-3.5 ${ESTILO_TARJETA[paso.estado]}`}>
      <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 transition-colors ${ESTILO_ICONO[paso.estado]}`}>
        <IconoEstadoPaso paso={paso} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2">
          <h3 className="text-base sm:text-lg font-extrabold text-[#14202B] leading-tight">{paso.nombre}</h3>
          <span className="text-xs sm:text-sm font-bold text-[#14202B]/70 shrink-0">{etiquetaProgreso}</span>
        </div>

        {paso.estado === 'lista' && paso.resumen && (
          <p className="text-xs sm:text-sm text-[#14202B]/80 mt-0.5 leading-snug">{paso.resumen}</p>
        )}
        {paso.estado === 'en_proceso' && (
          <p className="text-xs sm:text-sm text-[#14202B]/60 mt-0.5 leading-snug">Analizando...</p>
        )}
        {paso.estado === 'pendiente' && (
          <p className="text-xs sm:text-sm text-[#14202B]/60 mt-0.5 leading-snug">En espera</p>
        )}
        {paso.estado === 'fallida' && (
          <p className="text-xs sm:text-sm font-bold text-[#B5601F] mt-0.5 leading-snug">
            No pudimos leer este dato; el resto sigue avanzando.
          </p>
        )}

        <div
          role="progressbar"
          aria-valuenow={progreso}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Progreso de ${paso.nombre}`}
          className="w-full h-1.5 bg-[#EDE7DA] rounded-full overflow-hidden mt-2"
        >
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              paso.estado === 'lista' ? 'bg-[#1F4D2B]' : paso.estado === 'fallida' ? 'bg-[#E8833A]' : 'bg-[#6DBE7A]'
            }`}
            style={{ width: `${progreso}%` }}
          />
        </div>

        <span className="mt-2.5 inline-flex items-center gap-1.5 bg-[#EEF5FD] text-[#1B3654] text-xs font-bold px-3 py-1 rounded-full border border-[#D5E3F5]">
          {paso.estado === 'lista' ? `Listo · ${paso.fuente}` : paso.fuente}
        </span>
      </div>
    </li>
  );
};

export const TaskProgress: React.FC<TaskProgressProps> = ({
  tarea,
  onCompletado,
  tiempoEsperaMs = 1500,
  onSegundoPlano,
  onReintentar
}) => {
  const estaLista = tarea.estado === 'lista';
  const estaFallida = tarea.estado === 'fallida';
  const progreso = limitar(tarea.progreso);
  const ubicacion = [tarea.corregimiento_nombre, tarea.municipio_nombre].filter(Boolean).join(', ');

  const pasoActivo = tarea.pasos.find((p) => p.codigo === tarea.paso_activo_codigo);
  const etiquetaSatelite = pasoActivo?.estado === 'en_proceso' ? pasoActivo.fuente : 'Satélites de la NASA';

  // Mensaje para lectores de pantalla: cambia solo cuando cambia el paso o termina
  const anuncio = estaLista
    ? 'Diagnóstico del lote completo.'
    : estaFallida
      ? 'El diagnóstico no pudo completarse.'
      : pasoActivo
        ? `Analizando: ${pasoActivo.nombre}`
        : '';

  // Garantiza que onCompletado se llame una sola vez aunque el padre cambie la función
  const onCompletadoRef = useRef(onCompletado);
  const yaCompletadoRef = useRef(false);
  useEffect(() => {
    onCompletadoRef.current = onCompletado;
  }, [onCompletado]);

  const completar = useCallback(() => {
    if (yaCompletadoRef.current) return;
    yaCompletadoRef.current = true;
    onCompletadoRef.current?.();
  }, []);

  useEffect(() => {
    if (!estaLista) return;
    const timer = setTimeout(completar, tiempoEsperaMs);
    return () => clearTimeout(timer);
  }, [estaLista, tiempoEsperaMs, completar]);

  return (
    <section className="w-full max-w-[560px] mx-auto flex flex-col gap-4 px-4 py-4 sm:py-6" aria-labelledby="titulo-diagnostico">
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {anuncio}
      </div>

      {/* Estado general */}
      <div className="flex items-center justify-between bg-[#EBF3FC] border border-[#D5E3F5] rounded-full px-4 py-2">
        <span className="text-xs sm:text-sm font-extrabold tracking-wide uppercase text-[#14202B]">Datos de la NASA</span>
        <span className="flex items-center gap-1.5">
          <span className={`w-2.5 h-2.5 rounded-full ${estaFallida ? 'bg-[#E8833A]' : 'bg-[#1F4D2B]'} ${estaLista || estaFallida ? '' : 'animate-pulse'}`} />
          <span className="text-xs sm:text-sm font-black text-[#1F4D2B] tracking-wider">
            {estaLista ? 'Completo' : estaFallida ? 'Detenido' : 'Analizando'}
          </span>
        </span>
      </div>

      <header>
        <h1 id="titulo-diagnostico" className="text-2xl sm:text-3xl font-black text-[#14202B] leading-tight">
          {estaLista ? 'Ya leímos tu lote desde el espacio' : 'Estamos leyendo tu lote desde el espacio...'}
        </h1>
        <p className="text-base text-[#14202B]/80 mt-1.5 leading-relaxed">
          Analizamos <strong className="font-extrabold text-[#14202B]">{tarea.nombre_lote}</strong> (
          {formatearHectareas(tarea.area_ha)} ha{ubicacion ? ` en ${ubicacion}` : ''}) con datos satelitales.
        </p>
      </header>

      <SatelliteScan
        nombreLote={tarea.nombre_lote}
        areaHa={tarea.area_ha}
        poligono={tarea.poligono}
        etiquetaSatelite={etiquetaSatelite}
        estaEscaneando={!estaLista && !estaFallida}
      />

      {/* Progreso general */}
      <div className="bg-white rounded-2xl border-2 border-[#D2C8B5]/80 p-4 sm:p-5 shadow-sm flex flex-col gap-3">
        <div className="flex items-baseline justify-between">
          <span className="text-base sm:text-lg font-bold text-[#14202B]">Progreso del análisis</span>
          <span className="text-2xl sm:text-3xl font-black text-[#1F4D2B]">{progreso}%</span>
        </div>
        <div
          role="progressbar"
          aria-valuenow={progreso}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Progreso general del diagnóstico"
          className="w-full h-3 bg-[#E8E1D3] rounded-full overflow-hidden"
        >
          <div className="h-full bg-[#1F4D2B] rounded-full transition-all duration-500 ease-out" style={{ width: `${progreso}%` }} />
        </div>
        <p className="flex items-center gap-2 pt-1 text-sm sm:text-base font-bold text-[#14202B] leading-snug">
          <span className="shrink-0 text-[#1F4D2B]">
            {estaLista ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            ) : estaFallida ? null : (
              <Spinner />
            )}
          </span>
          {tarea.mensaje_estado}
        </p>
      </div>

      {/* Fuentes consultadas */}
      <ol className="flex flex-col gap-3" aria-label="Datos que estamos analizando">
        {tarea.pasos.map((paso) => (
          <TarjetaPaso key={paso.codigo} paso={paso} />
        ))}
      </ol>

      {/* Acciones */}
      <footer className="pt-2 pb-4 text-center">
        {estaLista && (
          <button
            type="button"
            onClick={completar}
            className="w-full min-h-[56px] bg-[#1F4D2B] hover:bg-[#16381F] text-white rounded-2xl font-black text-lg shadow-lg transition-all flex items-center justify-center gap-2 active:scale-[0.99]"
          >
            Ver mi lote
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        )}

        {estaFallida && onReintentar && (
          <button
            type="button"
            onClick={onReintentar}
            className="w-full min-h-[56px] bg-[#E8833A] hover:bg-[#C96D27] text-white rounded-2xl font-black text-lg"
          >
            Intentar de nuevo
          </button>
        )}

        {!estaLista && !estaFallida && (
          <>
            <p className="text-sm font-semibold text-[#14202B]/75">
              Esto toma menos de un minuto. Puedes quedarte en esta pantalla.
            </p>
            {onSegundoPlano && (
              <button
                type="button"
                onClick={onSegundoPlano}
                className="min-h-[56px] px-4 text-sm font-extrabold text-[#1F4D2B] underline hover:text-[#16381F]"
              >
                Continuar en segundo plano
              </button>
            )}
          </>
        )}
      </footer>
    </section>
  );
};
