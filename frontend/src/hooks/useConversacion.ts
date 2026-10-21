// src/hooks/useConversacion.ts
// La conversación con el Asistente SURCO para un lote: carga, envío (con el mensaje del productor
// pintado de una vez), notas de voz (transcribir y luego enviar), reintento y valoración.
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { ErrorApi, MensajeAsistente } from '../api/tipos';
import { enviarMensaje, obtenerConversacion, transcribirAudio, valorarMensaje } from '../api/services';
import { useSinConexion } from './useResumenInicio';

/** Un mensaje como se ve en pantalla: el del servidor más su estado local. */
export interface MensajeVista extends MensajeAsistente {
  /** Solo en mensajes del productor que todavía no llegan al servidor. */
  envio?: 'transcribiendo' | 'enviando' | 'fallido';
  /** La valoración que dio el productor a una respuesta del asistente. */
  valoracion?: boolean;
}

export type EstadoConversacion = 'cargando' | 'listo' | 'error';

export interface UseConversacion {
  estado: EstadoConversacion;
  error: ErrorApi | null;
  nombre: string | null;
  mensajes: MensajeVista[];
  /** El asistente está preparando una respuesta. */
  pensando: boolean;
  sinConexion: boolean;
  enviarTexto: (texto: string) => void;
  enviarAudio: (audio: Blob, duracion_s: number) => void;
  reintentarEnvio: (id: string) => void;
  valorar: (id: string, util: boolean) => void;
  recargar: () => void;
}

let consecutivo = 0;
const idLocal = () => `local-${Date.now()}-${++consecutivo}`;

function nuevoDelProductor(texto: string, duracion: number | null, envio: MensajeVista['envio']): MensajeVista {
  return {
    id: idLocal(),
    rol: 'productor',
    creado_en: new Date().toISOString(),
    texto,
    audio_duracion_s: duracion,
    tarjetas: [],
    enlaces: [],
    envio
  };
}

export function useConversacion(loteId: string | null): UseConversacion {
  const [estado, setEstado] = useState<EstadoConversacion>('cargando');
  const [error, setError] = useState<ErrorApi | null>(null);
  const [nombre, setNombre] = useState<string | null>(null);
  const [mensajes, setMensajes] = useState<MensajeVista[]>([]);
  const [pensando, setPensando] = useState(false);
  const [intento, setIntento] = useState(0);
  const sinConexion = useSinConexion();
  // Las notas de voz que fallaron al transcribirse se guardan para poder reintentar
  const audios = useRef(new Map<string, Blob>());

  useEffect(() => {
    if (!loteId) return;
    let cancelado = false;
    setEstado('cargando');
    setError(null);
    obtenerConversacion(loteId)
      .then((c) => {
        if (cancelado) return;
        setNombre(c.usuario.nombre);
        setMensajes(c.mensajes);
        setEstado('listo');
      })
      .catch((e: ErrorApi) => {
        if (cancelado) return;
        setError(e);
        setEstado('error');
      });
    return () => {
      cancelado = true;
    };
  }, [loteId, intento]);

  const actualizar = useCallback(
    (id: string, cambios: Partial<MensajeVista>) =>
      setMensajes((actuales) => actuales.map((m) => (m.id === id ? { ...m, ...cambios } : m))),
    []
  );

  /** Manda al servidor un mensaje del productor que ya está en pantalla. */
  const despachar = useCallback(
    async (id: string, texto: string, duracion: number | null) => {
      if (!loteId) return;
      actualizar(id, { envio: 'enviando' });
      setPensando(true);
      try {
        const respuesta = await enviarMensaje(loteId, texto, duracion);
        setMensajes((actuales) => [...actuales.map((m) => (m.id === id ? { ...m, envio: undefined } : m)), respuesta]);
      } catch {
        actualizar(id, { envio: 'fallido' });
      } finally {
        setPensando(false);
      }
    },
    [loteId, actualizar]
  );

  const transcribirYDespachar = useCallback(
    async (id: string, audio: Blob, duracion: number) => {
      actualizar(id, { envio: 'transcribiendo' });
      try {
        const { texto } = await transcribirAudio(audio);
        audios.current.delete(id);
        actualizar(id, { texto });
        await despachar(id, texto, duracion);
      } catch {
        audios.current.set(id, audio);
        actualizar(id, { envio: 'fallido' });
      }
    },
    [despachar, actualizar]
  );

  const enviarTexto = useCallback(
    (texto: string) => {
      const limpio = texto.trim();
      if (!limpio || pensando) return;
      const m = nuevoDelProductor(limpio, null, 'enviando');
      setMensajes((actuales) => [...actuales, m]);
      void despachar(m.id, limpio, null);
    },
    [despachar, pensando]
  );

  const enviarAudio = useCallback(
    (audio: Blob, duracion_s: number) => {
      if (pensando) return;
      const duracion = Math.max(1, Math.round(duracion_s));
      const m = nuevoDelProductor('', duracion, 'transcribiendo');
      setMensajes((actuales) => [...actuales, m]);
      void transcribirYDespachar(m.id, audio, duracion);
    },
    [transcribirYDespachar, pensando]
  );

  const reintentarEnvio = useCallback(
    (id: string) => {
      const m = mensajes.find((x) => x.id === id);
      if (!m || m.envio !== 'fallido' || pensando) return;
      const audio = audios.current.get(id);
      if (audio && m.audio_duracion_s !== null) void transcribirYDespachar(id, audio, m.audio_duracion_s);
      else void despachar(id, m.texto, m.audio_duracion_s);
    },
    [mensajes, pensando, despachar, transcribirYDespachar]
  );

  const valorar = useCallback((id: string, util: boolean) => {
    let anterior: boolean | undefined;
    setMensajes((actuales) =>
      actuales.map((m) => {
        if (m.id !== id) return m;
        anterior = m.valoracion;
        return { ...m, valoracion: util };
      })
    );
    valorarMensaje(id, util).catch(() => actualizar(id, { valoracion: anterior }));
  }, [actualizar]);

  const recargar = useCallback(() => setIntento((n) => n + 1), []);

  return { estado, error, nombre, mensajes, pensando, sinConexion, enviarTexto, enviarAudio, reintentarEnvio, valorar, recargar };
}
