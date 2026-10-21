// src/hooks/useGrabadora.ts
// Graba una nota de voz con MediaRecorder. El permiso del micrófono se pide solo al empezar.
// Mientras graba entrega el tiempo y el nivel de la voz (para dibujar la onda) y corta a los 60 s.
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { MAX_GRABACION_S, tipoAudioSoportado } from '../lib/asistente';

export type EstadoGrabadora = 'inactivo' | 'pidiendo_permiso' | 'grabando' | 'sin_permiso' | 'sin_microfono' | 'no_soportado';

/** Barras de la onda en vivo. */
export const BARRAS_ONDA = 28;
/** Una grabación más corta que esto se descarta (fue un toque sin querer). */
const MINIMO_S = 0.6;

export interface UseGrabadora {
  estado: EstadoGrabadora;
  segundos: number;
  /** Nivel de la voz de 0 a 1, una barra por cada ~100 ms; la última es la más reciente. */
  niveles: number[];
  iniciar: () => Promise<void>;
  /** Termina y entrega el audio a onListo. */
  terminar: () => void;
  /** Termina y descarta el audio. */
  cancelar: () => void;
  /** Vuelve de "sin permiso" o "sin micrófono" al estado inicial. */
  descartarAviso: () => void;
}

const nivelesVacios = () => Array.from({ length: BARRAS_ONDA }, () => 0);

export function useGrabadora(onListo: (audio: Blob, duracion_s: number) => void): UseGrabadora {
  const [estado, setEstado] = useState<EstadoGrabadora>('inactivo');
  const [segundos, setSegundos] = useState(0);
  const [niveles, setNiveles] = useState<number[]>(nivelesVacios);

  const grabadora = useRef<MediaRecorder | null>(null);
  const flujo = useRef<MediaStream | null>(null);
  const contexto = useRef<AudioContext | null>(null);
  const temporizador = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const cuadro = useRef<number | undefined>(undefined);
  const inicio = useRef(0);
  const descartar = useRef(false);
  const onListoRef = useRef(onListo);
  useEffect(() => {
    onListoRef.current = onListo;
  }, [onListo]);

  const liberar = useCallback(() => {
    clearInterval(temporizador.current);
    if (cuadro.current !== undefined) cancelAnimationFrame(cuadro.current);
    flujo.current?.getTracks().forEach((t) => t.stop());
    void contexto.current?.close().catch(() => undefined);
    flujo.current = null;
    contexto.current = null;
    grabadora.current = null;
  }, []);

  const detener = useCallback((descartarAudio: boolean) => {
    const g = grabadora.current;
    if (!g || g.state === 'inactive') return;
    descartar.current = descartarAudio;
    g.stop();
  }, []);

  const terminar = useCallback(() => detener(false), [detener]);
  const cancelar = useCallback(() => detener(true), [detener]);

  /** La onda en vivo: el volumen (RMS) del micrófono, si el navegador tiene Web Audio. */
  const medirVoz = useCallback((stream: MediaStream) => {
    if (typeof AudioContext === 'undefined') return;
    try {
      const ctx = new AudioContext();
      const analizador = ctx.createAnalyser();
      analizador.fftSize = 512;
      ctx.createMediaStreamSource(stream).connect(analizador);
      contexto.current = ctx;
      const muestras = new Uint8Array(analizador.fftSize);
      let ultimo = 0;
      const paso = (t: number) => {
        if (t - ultimo >= 100) {
          ultimo = t;
          analizador.getByteTimeDomainData(muestras);
          let suma = 0;
          for (const m of muestras) suma += ((m - 128) / 128) ** 2;
          const nivel = Math.min(1, Math.sqrt(suma / muestras.length) * 4);
          setNiveles((previos) => [...previos.slice(1), nivel]);
        }
        cuadro.current = requestAnimationFrame(paso);
      };
      cuadro.current = requestAnimationFrame(paso);
    } catch {
      // Sin onda en vivo: la grabación sigue igual
    }
  }, []);

  const iniciar = useCallback(async () => {
    if (grabadora.current) return;
    if (typeof MediaRecorder === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setEstado('no_soportado');
      return;
    }
    setEstado('pidiendo_permiso');
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      const nombre = e instanceof DOMException ? e.name : '';
      setEstado(nombre === 'NotFoundError' || nombre === 'OverconstrainedError' ? 'sin_microfono' : 'sin_permiso');
      return;
    }

    const tipo = tipoAudioSoportado((t) => MediaRecorder.isTypeSupported(t));
    const g = tipo ? new MediaRecorder(stream, { mimeType: tipo }) : new MediaRecorder(stream);
    const partes: Blob[] = [];
    g.ondataavailable = (ev) => {
      if (ev.data.size > 0) partes.push(ev.data);
    };
    g.onstop = () => {
      const duracion = (Date.now() - inicio.current) / 1000;
      liberar();
      setEstado('inactivo');
      setSegundos(0);
      setNiveles(nivelesVacios());
      if (!descartar.current && duracion >= MINIMO_S && partes.length > 0) {
        onListoRef.current(new Blob(partes, { type: g.mimeType || tipo || 'audio/webm' }), Math.min(duracion, MAX_GRABACION_S));
      }
    };

    flujo.current = stream;
    grabadora.current = g;
    descartar.current = false;
    inicio.current = Date.now();
    g.start(250);
    setSegundos(0);
    setEstado('grabando');
    medirVoz(stream);
    temporizador.current = setInterval(() => {
      const s = (Date.now() - inicio.current) / 1000;
      setSegundos(Math.min(s, MAX_GRABACION_S));
      if (s >= MAX_GRABACION_S) detener(false);
    }, 200);
  }, [liberar, medirVoz, detener]);

  const descartarAviso = useCallback(() => setEstado('inactivo'), []);

  // Si se sale de la pantalla grabando, se descarta y se apaga el micrófono
  useEffect(
    () => () => {
      descartar.current = true;
      if (grabadora.current && grabadora.current.state !== 'inactive') grabadora.current.stop();
      liberar();
    },
    [liberar]
  );

  return { estado, segundos, niveles, iniciar, terminar, cancelar, descartarAviso };
}
