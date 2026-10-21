// src/api/mocks/asistente.ts
// Datos de demostración del Asistente SURCO mientras el backend no tenga sus endpoints.
// Solo los usa services.ts cuando NEXT_PUBLIC_USAR_MOCKS incluye "asistente" (ver PENDIENTES-BACKEND.md).
// Las respuestas salen de los mismos datos de demo de Inicio y del Plan, para que no se contradigan.
import type { Conversacion, ErrorApi, MensajeAsistente, Procedencia, ResumenLote, TarjetaDato, Transcripcion } from '../tipos';
import { resumenDemo } from './inicio';
import { LOTES_DEMO, planDemo } from './plan';

export type EscenarioAsistente = 'con-historia' | 'nuevo' | 'falla-envio';
export const ESCENARIOS_ASISTENTE: readonly EscenarioAsistente[] = ['con-historia', 'nuevo', 'falla-envio'];

export const NOMBRE_DEMO = 'Ernesto';
export const PREGUNTA_VOZ_DEMO = '¿Será que riego el maíz esta semana?';

function isoDia(fecha: Date): string {
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

function haceDias(dias: number, ahora: Date): Date {
  const d = new Date(ahora);
  d.setDate(d.getDate() - dias);
  return d;
}

const fuente = (nombre: string, fecha: Date | null): Procedencia => ({ fuente: nombre, fecha: fecha ? isoDia(fecha) : null });
const nombreLote = (lote_id: string) => LOTES_DEMO.find((l) => l.id === lote_id)?.nombre ?? 'su lote';

let consecutivo = 0;
const nuevoId = (prefijo: string) => `${prefijo}-${Date.now()}-${++consecutivo}`;

function mensaje(parcial: Partial<MensajeAsistente> & Pick<MensajeAsistente, 'rol' | 'texto'>): MensajeAsistente {
  return {
    id: nuevoId(parcial.rol),
    creado_en: new Date().toISOString(),
    audio_duracion_s: null,
    tarjetas: [],
    enlaces: [],
    ...parcial
  };
}

// --- Respuestas según la pregunta ---

function tarjetasRiego(ahora: Date): TarjetaDato[] {
  return [
    { etiqueta: 'Humedad de la tierra', valor: 'Baja', unidad: null, procedencia: fuente('NASA SMAP', haceDias(2, ahora)) },
    { etiqueta: 'Lluvia de los últimos 7 días', valor: '3', unidad: 'mm', procedencia: fuente('NASA POWER', ahora) }
  ];
}

/** La respuesta del asistente a una pregunta, con los datos de demo del lote. Exportada para las pruebas. */
export function respuestaDemo(pregunta: string, lote_id: string, nombre = NOMBRE_DEMO, ahora: Date = new Date()): MensajeAsistente {
  const texto = pregunta.toLowerCase();
  const lote = nombreLote(lote_id);
  const verLote = { texto: 'Ver en mi lote', ruta: `/lotes/${encodeURIComponent(lote_id)}` };
  const verPlan = { texto: 'Ver mi plan', ruta: `/plan?lote=${encodeURIComponent(lote_id)}` };

  // Temas sobre los que no hay datos confiables: se dice claro y se remite al técnico
  if (/plaga|insect|gusano|hongo|abono|fertiliz|agroqu|fumig|veneno|precio|a c[oó]mo|cu[aá]nto vale|cu[aá]nto pagan/.test(texto)) {
    return mensaje({
      rol: 'asistente',
      texto:
        'Sobre eso no le puedo responder: no tengo datos confiables para su lote. Consulte con su técnico agrícola. ' +
        'Yo le ayudo con riego, siembra, suelo y lluvia.'
    });
  }

  const porQue = /por qu[eé] me recomiendan (.+?)\??$/.exec(texto);
  if (porQue) {
    const plan = planDemo(lote_id, ahora);
    const buscado = porQue[1].trim();
    const rotacion = plan.rotaciones.find((r) => r.secuencia.some((c) => c.nombre.toLowerCase() === buscado));
    const cultivo = rotacion?.secuencia.find((c) => c.nombre.toLowerCase() === buscado)?.nombre;
    if (rotacion && cultivo) {
      return mensaje({
        rol: 'asistente',
        texto: `Le recomendamos ${cultivo.toLowerCase()} porque ${rotacion.razones[0].texto.charAt(0).toLowerCase()}${rotacion.razones[0].texto.slice(1)} ${rotacion.razones[1]?.texto ?? ''}`.trim(),
        tarjetas: [
          { etiqueta: 'Le va bien', valor: `${rotacion.frecuencia_exito} de cada 10`, unidad: 'años', procedencia: rotacion.razones[0].procedencia },
          { etiqueta: 'Agua que se ahorra con la rotación', valor: rotacion.agua_ahorrada_m3.toLocaleString('es-CO'), unidad: 'm³', procedencia: fuente('NASA POWER', ahora) }
        ],
        enlaces: [verPlan]
      });
    }
  }

  if (/rieg|regar|regu[eé]|agua|seca/.test(texto)) {
    // Un lote sin cultivo no se riega: la respuesta no puede hablar de un maíz que no existe
    if (!resumenLoteDemo(lote_id).cultivo) {
      return mensaje({
        rol: 'asistente',
        texto: `Su lote ${lote} no tiene un cultivo registrado, así que por ahora no hace falta regar. La tierra está seca: si va a sembrar, la mejor época es la primera quincena de marzo, con las lluvias.`,
        tarjetas: tarjetasRiego(ahora),
        enlaces: [verPlan]
      });
    }
    return mensaje({
      rol: 'asistente',
      texto: `Sí, ${nombre}. La tierra de su lote ${lote} está seca para un maíz en floración. Riegue esta semana unos 450 m³ por hectárea.`,
      tarjetas: tarjetasRiego(ahora),
      enlaces: [verLote]
    });
  }

  if (/sembr|siembr|semestre|cultivo|rotaci/.test(texto)) {
    return mensaje({
      rol: 'asistente',
      texto: 'Para el próximo semestre, la mejor opción para su lote es maíz, luego soya y luego sorgo. La mejor época para sembrar el maíz es la primera quincena de marzo.',
      tarjetas: [{ etiqueta: 'Le va bien', valor: '8 de cada 10', unidad: 'años', procedencia: fuente('NASA POWER', ahora) }],
      enlaces: [verPlan]
    });
  }

  if (/suelo|tierra/.test(texto)) {
    return mensaje({
      rol: 'asistente',
      texto: 'Su suelo está en 72 de 100 y subió 9 puntos en el último año. La soya de su rotación le ha dejado nitrógeno natural.',
      tarjetas: [{ etiqueta: 'Salud del suelo', valor: '72', unidad: 'de 100', procedencia: fuente('SoilGrids', null) }],
      enlaces: [verLote]
    });
  }

  if (/lluv|llov|clima|tiempo/.test(texto)) {
    return mensaje({
      rol: 'asistente',
      texto: 'Esta semana viene seca: casi no ha llovido y hoy la probabilidad de lluvia es baja. Por eso conviene regar el maíz.',
      tarjetas: [
        { etiqueta: 'Lluvia de los últimos 7 días', valor: '3', unidad: 'mm', procedencia: fuente('NASA POWER', ahora) },
        { etiqueta: 'Probabilidad de lluvia hoy', valor: '10', unidad: '%', procedencia: fuente('NASA POWER', ahora) }
      ],
      enlaces: [verLote]
    });
  }

  return mensaje({
    rol: 'asistente',
    texto: 'Por ahora le puedo responder sobre riego, siembra, suelo y lluvia en su lote. ¿Me lo pregunta de otra forma?'
  });
}

export function conversacionDemo(escenario: EscenarioAsistente, lote_id: string, ahora: Date = new Date()): Conversacion {
  // La conversación de ejemplo habla del maíz de La Vega: en un lote sin cultivo se empieza de cero
  if (escenario === 'nuevo' || !resumenLoteDemo(lote_id).cultivo) return { usuario: { nombre: NOMBRE_DEMO }, lote_id, mensajes: [] };
  const hace = (min: number) => new Date(ahora.getTime() - min * 60_000).toISOString();
  return {
    usuario: { nombre: NOMBRE_DEMO },
    lote_id,
    mensajes: [
      { ...mensaje({ rol: 'productor', texto: PREGUNTA_VOZ_DEMO, audio_duracion_s: 4 }), id: 'demo-1', creado_en: hace(12) },
      { ...respuestaDemo(PREGUNTA_VOZ_DEMO, lote_id, NOMBRE_DEMO, ahora), id: 'demo-2', creado_en: hace(12) }
    ]
  };
}

export function resumenLoteDemo(lote_id: string): ResumenLote {
  const base = resumenDemo('historia').lote_principal;
  const lote = LOTES_DEMO.find((l) => l.id === lote_id) ?? LOTES_DEMO[0];
  if (!base) throw new Error('El mock de Inicio siempre trae lote');
  if (lote.id === LOTES_DEMO[0].id) return { ...base, id: lote.id };
  return { ...base, id: lote.id, nombre: lote.nombre, area_ha: lote.area_ha, cultivo: null };
}

// --- Funciones que usa services.ts ---

let fallasPendientes = 1;
const esperar = (ms: number) => new Promise<void>((resolver) => setTimeout(resolver, ms));

export async function obtenerConversacionMock(escenario: EscenarioAsistente, lote_id: string): Promise<Conversacion> {
  await esperar(500);
  return conversacionDemo(escenario, lote_id);
}

export async function enviarMensajeMock(escenario: EscenarioAsistente, lote_id: string, texto: string): Promise<MensajeAsistente> {
  await esperar(1400);
  if (escenario === 'falla-envio' && fallasPendientes > 0) {
    fallasPendientes--;
    throw { codigo: 'HTTP_503', mensaje: 'No pudimos enviar su pregunta.' } satisfies ErrorApi;
  }
  return respuestaDemo(texto, lote_id);
}

export async function transcribirAudioMock(): Promise<Transcripcion> {
  await esperar(900);
  return { texto: PREGUNTA_VOZ_DEMO };
}

export async function valorarMensajeMock(): Promise<void> {
  await esperar(250);
}

export async function obtenerResumenLoteMock(lote_id: string): Promise<ResumenLote> {
  await esperar(400);
  return resumenLoteDemo(lote_id);
}
