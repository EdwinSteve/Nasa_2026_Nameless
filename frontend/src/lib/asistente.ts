// src/lib/asistente.ts
// Reglas y textos del Asistente SURCO. Sin React: se prueban solas.

export const PREGUNTAS_BASE = [
  '¿Debo regar hoy?',
  '¿Qué siembro el próximo semestre?',
  '¿Cómo está mi suelo?',
  '¿Cómo viene la lluvia esta semana?'
] as const;

/** Las preguntas sugeridas; si el productor llega desde el Plan con un cultivo, esa va primero. */
export function preguntasSugeridas(cultivo: string | null): string[] {
  const base: string[] = [...PREGUNTAS_BASE];
  return cultivo ? [`¿Por qué me recomiendan ${cultivo.toLowerCase()}?`, ...base] : base;
}

// --- Voz ---

export const MAX_GRABACION_S = 60;
/** Si el dedo se queda más que esto sobre el micrófono, es "mantener presionado": al soltar se envía. */
export const UMBRAL_MANTENER_MS = 350;
/** Mientras se mantiene presionado, deslizar esta distancia hacia la izquierda cancela. */
export const DISTANCIA_CANCELAR_PX = 80;

/** 18 → "0:18"; 75 → "1:15". */
export function formatearDuracion(segundos: number): string {
  const total = Math.max(0, Math.round(segundos));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
}

/** "0:18" en palabras para lectores de pantalla: "18 segundos", "1 minuto y 15 segundos". */
export function duracionEnPalabras(segundos: number): string {
  const total = Math.max(0, Math.round(segundos));
  const min = Math.floor(total / 60);
  const seg = total % 60;
  const partes = [
    min ? `${min} ${min === 1 ? 'minuto' : 'minutos'}` : null,
    seg || !min ? `${seg} ${seg === 1 ? 'segundo' : 'segundos'}` : null
  ].filter(Boolean);
  return partes.join(' y ');
}

const TIPOS_AUDIO = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'] as const;

/** El primer formato de audio que el navegador sabe grabar ("" = que elija él). Safari solo graba mp4. */
export function tipoAudioSoportado(esSoportado: (tipo: string) => boolean): string {
  return TIPOS_AUDIO.find((t) => esSoportado(t)) ?? '';
}

/** Alturas (de 0,2 a 1) de una onda decorativa para una nota de voz; la misma semilla da la misma onda. */
export function ondaDecorativa(semilla: string, barras = 28): number[] {
  let h = 2166136261;
  for (const c of semilla) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
  return Array.from({ length: barras }, (_, i) => {
    h = Math.imul(h ^ (i + 1), 16777619);
    const ruido = ((h >>> 0) % 1000) / 1000;
    const envolvente = Math.sin((Math.PI * (i + 0.5)) / barras); // más alta en el medio
    return Math.round((0.2 + 0.8 * envolvente * (0.45 + 0.55 * ruido)) * 100) / 100;
  });
}

// --- Fechas de los mensajes ---

const hora = new Intl.DateTimeFormat('es-CO', { hour: 'numeric', minute: '2-digit' });
const diaHora = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });

/** "7:14 a. m." si es de hoy; "12 oct, 7:14 a. m." si es de otro día. */
export function horaMensaje(iso: string, ahora: Date = new Date()): string {
  const fecha = new Date(iso);
  const mismoDia = fecha.toDateString() === ahora.toDateString();
  return (mismoDia ? hora : diaHora).format(fecha).replace(/ /g, ' ');
}
