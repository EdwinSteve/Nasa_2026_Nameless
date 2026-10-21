// Barra de abajo del chat: UN micrófono grande (lo principal), el campo de texto y enviar.
// El micrófono se toca para empezar y se toca para enviar, o se mantiene presionado y se suelta
// para enviar; mientras se mantiene, deslizar a la izquierda cancela. Con teclado, Enter o Espacio.
'use client';

import { useId, useRef, useState, type FormEvent, type MouseEvent, type PointerEvent } from 'react';
import type { UseGrabadora } from '../../hooks/useGrabadora';
import { DISTANCIA_CANCELAR_PX, formatearDuracion, MAX_GRABACION_S, UMBRAL_MANTENER_MS } from '../../lib/asistente';
import { IconoCerrar, IconoEnviar, IconoMicrofono } from '../iconos/Iconos';
import { OndaVoz } from './OndaVoz';

interface Props {
  grabadora: UseGrabadora;
  sinConexion: boolean;
  pensando: boolean;
  onEnviarTexto: (texto: string) => void;
}

export function BarraEntrada({ grabadora, sinConexion, pensando, onEnviarTexto }: Props) {
  const idNota = useId();
  const idCampo = useId();
  const [texto, setTexto] = useState('');
  const [manteniendo, setManteniendo] = useState(false);
  const toque = useRef<{ inicio: number; x: number } | null>(null);
  const grabando = grabadora.estado === 'grabando';
  const ocupado = sinConexion || pensando;

  const enviar = (e: FormEvent) => {
    e.preventDefault();
    if (!texto.trim() || ocupado) return;
    onEnviarTexto(texto);
    setTexto('');
  };

  const alPresionar = (e: PointerEvent<HTMLButtonElement>) => {
    if (ocupado || e.button !== 0) return;
    if (grabando) {
      grabadora.terminar();
      return;
    }
    e.currentTarget.setPointerCapture(e.pointerId);
    toque.current = { inicio: Date.now(), x: e.clientX };
    setManteniendo(true);
    void grabadora.iniciar();
  };

  const alMover = (e: PointerEvent<HTMLButtonElement>) => {
    if (!toque.current || !manteniendo) return;
    if (toque.current.x - e.clientX >= DISTANCIA_CANCELAR_PX) {
      toque.current = null;
      setManteniendo(false);
      grabadora.cancelar();
    }
  };

  const alSoltar = () => {
    if (!toque.current) return;
    const mantuvo = Date.now() - toque.current.inicio >= UMBRAL_MANTENER_MS;
    toque.current = null;
    setManteniendo(false);
    // Si mantuvo presionado, al soltar se envía; si fue un toque, sigue grabando hasta el próximo toque
    if (mantuvo) grabadora.terminar();
  };

  // El clic que sigue a un pointerdown ya se atendió; aquí solo llega el teclado (detail = 0)
  const alClic = (e: MouseEvent<HTMLButtonElement>) => {
    if (e.detail !== 0 || ocupado) return;
    if (grabando) grabadora.terminar();
    else void grabadora.iniciar();
  };

  const etiquetaMicrofono = grabando ? 'Enviar nota de voz' : 'Grabar una nota de voz';

  return (
    <div className="flex flex-col gap-2">
      <p id={idNota} className="text-center text-sm text-tinta/75">
        Soy un asistente con inteligencia artificial. Mis respuestas no reemplazan a su técnico agrícola.
      </p>
      {sinConexion && (
        <p role="status" className="text-center text-base font-semibold text-[#A33333]">
          Necesita conexión para preguntar.
        </p>
      )}

      <form onSubmit={enviar} className="flex items-center gap-2" aria-describedby={idNota}>
        <button
          type="button"
          onPointerDown={alPresionar}
          onPointerMove={alMover}
          onPointerUp={alSoltar}
          onPointerCancel={alSoltar}
          onClick={alClic}
          onContextMenu={(e) => e.preventDefault()}
          disabled={ocupado}
          aria-label={etiquetaMicrofono}
          aria-pressed={grabando}
          className={`flex h-16 w-16 shrink-0 touch-none select-none items-center justify-center rounded-full text-white shadow-md transition-transform disabled:bg-tinta/30 disabled:shadow-none ${
            grabando ? 'scale-105 bg-[#C0392B] ring-4 ring-[#C0392B]/25' : 'bg-campo hover:bg-[#16381F] active:scale-95'
          }`}
        >
          {grabando ? <IconoEnviar tamano={28} /> : <IconoMicrofono tamano={30} />}
        </button>

        {grabando ? (
          <div className="flex min-h-14 min-w-0 flex-1 items-center gap-3 rounded-full border-2 border-[#C0392B]/30 bg-white px-4" aria-live="polite">
            <span aria-hidden="true" className="h-3 w-3 shrink-0 animate-pulse rounded-full bg-[#C0392B] motion-reduce:animate-none" />
            <span className="shrink-0 text-base font-bold tabular-nums text-tinta">
              {formatearDuracion(grabadora.segundos)}
              <span className="text-tinta/60"> / {formatearDuracion(MAX_GRABACION_S)}</span>
            </span>
            <OndaVoz niveles={grabadora.niveles} clase="bg-[#C0392B]/70" />
            <span className="sr-only">Grabando.</span>
          </div>
        ) : (
          <>
            <label htmlFor={idCampo} className="sr-only">
              Su pregunta
            </label>
            <input
              id={idCampo}
              type="text"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              disabled={sinConexion}
              placeholder={sinConexion ? 'Sin conexión' : 'Escriba o hable…'}
              autoComplete="off"
              enterKeyHint="send"
              className="min-h-14 min-w-0 flex-1 rounded-full border-2 border-borde bg-white px-5 text-base text-tinta placeholder:text-tinta/55 focus:border-campo focus:outline-none disabled:bg-[#EDE7DA]"
            />
          </>
        )}

        {grabando ? (
          <button
            type="button"
            onClick={grabadora.cancelar}
            aria-label="Cancelar la nota de voz"
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-2 border-borde bg-white text-tinta hover:bg-tinta/5"
          >
            <IconoCerrar tamano={24} />
          </button>
        ) : (
          <button
            type="submit"
            disabled={ocupado || !texto.trim()}
            aria-label="Enviar pregunta"
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-campo text-white hover:bg-[#16381F] disabled:bg-tinta/25"
          >
            <IconoEnviar tamano={24} />
          </button>
        )}
      </form>

      {grabando && (
        <p className="text-center text-sm font-semibold text-tinta/80">
          {manteniendo ? 'Suelte para enviar · Deslice a la izquierda para cancelar' : 'Toque para enviar · Use la X para cancelar'}
        </p>
      )}
      {grabadora.estado === 'pidiendo_permiso' && <p className="text-center text-sm text-tinta/75">Esperando el permiso del micrófono…</p>}
    </div>
  );
}
