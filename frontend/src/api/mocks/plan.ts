// src/api/mocks/plan.ts
// Datos de demostración del plan de siembra (valle de Neiva) mientras el backend no tenga sus endpoints.
// Solo los usa services.ts cuando NEXT_PUBLIC_USAR_MOCKS incluye "plan" (ver PENDIENTES-BACKEND.md).
// Las fechas y los meses se calculan a partir de hoy: nada queda fijo.
import type {
  ErrorApi,
  IniciarPlanResponse,
  LluviaMensual,
  LoteResumen,
  Plan,
  PlanAceptado,
  Procedencia,
  ResultadoEscenario,
  TareaPlanResponse,
  VentanaSiembra
} from '../tipos';

export type EscenarioPlan = 'con-plan' | 'sin-plan' | 'sin-diagnostico' | 'calculando' | 'error';
export const ESCENARIOS_PLAN: readonly EscenarioPlan[] = ['con-plan', 'sin-plan', 'sin-diagnostico', 'calculando', 'error'];

export const PLAN_DEMO_ID = 'plan-demo';
const TAREA_DEMO_ID = 'tarea-plan-demo';
/** Lo que tarda la tarea simulada en armar el plan. */
export const DURACION_TAREA_MS = 6000;

function isoDia(fecha: Date): string {
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

function sumarDias(fecha: Date, dias: number): Date {
  const copia = new Date(fecha);
  copia.setDate(copia.getDate() + dias);
  return copia;
}

const hoy = () => new Date();
const fuente = (nombre: string, fecha: Date | null = hoy()): Procedencia => ({ fuente: nombre, fecha: fecha ? isoDia(fecha) : null });

export const LOTES_DEMO: LoteResumen[] = [
  { id: 'lote-demo-historia', nombre: 'La Vega', area_ha: 6.4 },
  { id: 'lote-demo-guadual', nombre: 'El Guadual', area_ha: 3.2 }
];

export function planDemo(lote_id: string, ahora: Date = hoy()): Plan {
  const clima = fuente('NASA POWER', ahora);
  const suelo = fuente('SoilGrids', null);
  const pronostico = fuente('NOAA CPC', sumarDias(ahora, -6));
  return {
    id: PLAN_DEMO_ID,
    lote_id,
    calculado_en: sumarDias(ahora, -1).toISOString(),
    rotaciones: [
      {
        id: 'rot-maiz-soya-sorgo',
        grado: 'A',
        secuencia: [
          { cultivo_id: 'maiz', nombre: 'Maíz' },
          { cultivo_id: 'soya', nombre: 'Soya' },
          { cultivo_id: 'sorgo', nombre: 'Sorgo' }
        ],
        frecuencia_exito: 8,
        agua_ahorrada_m3: 2100,
        aporte_nitrogeno: 'La soya le deja al sorgo unos 60 kg de nitrógeno por hectárea',
        razones: [
          { texto: 'Las lluvias de marzo y abril alcanzan para el maíz en 8 de cada 10 años.', procedencia: clima },
          { texto: 'El sorgo aguanta bien los meses secos de mitad de año.', procedencia: clima },
          { texto: 'Su suelo guarda bien el agua para los tres cultivos.', procedencia: suelo }
        ]
      },
      {
        id: 'rot-arroz-soya-maiz',
        grado: 'B',
        secuencia: [
          { cultivo_id: 'arroz_riego', nombre: 'Arroz' },
          { cultivo_id: 'soya', nombre: 'Soya' },
          { cultivo_id: 'maiz', nombre: 'Maíz' }
        ],
        frecuencia_exito: 7,
        agua_ahorrada_m3: 900,
        aporte_nitrogeno: 'La soya le deja al maíz unos 60 kg de nitrógeno por hectárea',
        razones: [
          { texto: 'El arroz rinde bien con el calor de su zona, pero pide más riego.', procedencia: clima },
          { texto: 'Se espera un año sin El Niño ni La Niña fuertes.', procedencia: pronostico }
        ]
      },
      {
        id: 'rot-sorgo-mani-maiz',
        grado: 'B',
        secuencia: [
          { cultivo_id: 'sorgo', nombre: 'Sorgo' },
          { cultivo_id: 'mani', nombre: 'Maní' },
          { cultivo_id: 'maiz', nombre: 'Maíz' }
        ],
        frecuencia_exito: 7,
        agua_ahorrada_m3: 1500,
        aporte_nitrogeno: 'El maní le deja al maíz unos 40 kg de nitrógeno por hectárea',
        razones: [
          { texto: 'El maní se da bien en suelos sueltos como el suyo.', procedencia: suelo },
          { texto: 'Gasta poca agua: sorgo y maní aguantan la época seca.', procedencia: clima }
        ]
      }
    ],
    ranking: [
      { cultivo_id: 'arroz_riego', nombre: 'Arroz', ip: 0.83, apto: true, razon_no_apto: null },
      { cultivo_id: 'maiz', nombre: 'Maíz', ip: 0.71, apto: true, razon_no_apto: null },
      { cultivo_id: 'sorgo', nombre: 'Sorgo', ip: 0.67, apto: true, razon_no_apto: null },
      { cultivo_id: 'cafe', nombre: 'Café', ip: 0.12, apto: false, razon_no_apto: 'Su zona es muy caliente para el café.' },
      { cultivo_id: 'cacao', nombre: 'Cacao', ip: 0.61, apto: true, razon_no_apto: null },
      { cultivo_id: 'soya', nombre: 'Soya', ip: 0.56, apto: true, razon_no_apto: null },
      { cultivo_id: 'frijol', nombre: 'Fríjol', ip: 0.46, apto: true, razon_no_apto: null }
    ]
  };
}

// Lluvia típica del valle de Neiva por mes (enero a diciembre), en mm: dos temporadas de lluvia al año.
const LLUVIA_MM = [90, 110, 160, 190, 150, 70, 45, 35, 70, 170, 180, 110];
const NOTA_MES: Array<string | null> = [
  'Bajan las lluvias: buen momento para cosechar.',
  'Empiezan a volver las lluvias.',
  'Buena época para sembrar maíz.',
  'Las lluvias más fuertes del año.',
  'Siguen las lluvias, pero van bajando.',
  'Empieza la época seca.',
  'El mes más seco: planee el riego.',
  'Mes muy seco: el sorgo lo aguanta mejor.',
  'Vuelven algunas lluvias.',
  'Buenas lluvias para que germine la semilla.',
  'Lluvias seguidas: revise que el agua no se encharque.',
  null
];

export function lluviasDemo(ahora: Date = hoy(), meses = 6): LluviaMensual[] {
  return Array.from({ length: meses }, (_, i) => {
    const d = new Date(ahora.getFullYear(), ahora.getMonth() + i, 1);
    const mm = LLUVIA_MM[d.getMonth()];
    return {
      mes: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      lluvia_mm: mm,
      nivel: mm < 80 ? 'seco' : mm > 150 ? 'lluvioso' : 'normal',
      nota: NOTA_MES[d.getMonth()],
      procedencia: fuente('NASA POWER', ahora)
    };
  });
}

// Día (contado desde hoy) en que cada cultivo tiene su mejor época de siembra, y qué tan alto llega.
const PICO: Record<string, { dia: number; alto: number }> = {
  maiz: { dia: 140, alto: 8 },
  arroz_riego: { dia: 126, alto: 8 },
  sorgo: { dia: 154, alto: 7 },
  soya: { dia: 147, alto: 6 },
  cacao: { dia: 133, alto: 6 },
  frijol: { dia: 140, alto: 5 },
  mani: { dia: 161, alto: 7 },
  cafe: { dia: 140, alto: 2 }
};

export function ventanaDemo(cultivo_id: string, ahora: Date = hoy()): VentanaSiembra {
  const pico = PICO[cultivo_id] ?? { dia: 140, alto: 6 };
  // Una semana entre puntos durante 6 meses. Hay una temporada fuerte (la del pico) y una menor al inicio.
  const puntos = Array.from({ length: 26 }, (_, i) => {
    const dia = i * 7;
    const fuerte = pico.alto * Math.exp(-(((dia - pico.dia) / 40) ** 2));
    const menor = (pico.alto - 3) * Math.exp(-(((dia - 7) / 20) ** 2));
    const frecuencia = Math.max(1, Math.min(10, Math.round(Math.max(fuerte, menor, 1.5))));
    return { fecha: isoDia(sumarDias(ahora, dia)), frecuencia_exito: frecuencia };
  });
  const maximo = Math.max(...puntos.map((p) => p.frecuencia_exito));
  // La mejor época: los puntos seguidos con la frecuencia más alta alrededor del pico
  let inicio = Math.min(puntos.length - 1, Math.round(pico.dia / 7));
  while (puntos[inicio].frecuencia_exito < maximo && inicio > 0) inicio--;
  let fin = inicio;
  while (inicio > 0 && puntos[inicio - 1].frecuencia_exito === maximo) inicio--;
  while (fin + 1 < puntos.length && puntos[fin + 1].frecuencia_exito === maximo) fin++;
  return {
    cultivo_id,
    puntos,
    mejor_inicio: puntos[inicio].fecha,
    mejor_fin: puntos[fin].fecha,
    razones: [
      { texto: 'En esas semanas llegan las lluvias justo cuando la planta más agua necesita.', procedencia: fuente('NASA POWER', ahora) },
      { texto: 'La tierra de su lote tiene buena humedad para que germine la semilla.', procedencia: fuente('NASA SMAP', sumarDias(ahora, -2)) },
      { texto: 'Se espera un año sin El Niño ni La Niña fuertes.', procedencia: fuente('NOAA CPC', sumarDias(ahora, -6)) }
    ]
  };
}

/** Cuántos años de cada 10 le iría bien si el clima cambia. Menos lluvia o más calor bajan la cifra. */
export function escenarioDemo(base: number, delta_lluvia_pct: number, delta_temp_c: number): number {
  const porLluvia = delta_lluvia_pct < 0 ? delta_lluvia_pct * 0.08 : -delta_lluvia_pct * 0.03;
  const valor = base + porLluvia - delta_temp_c * 0.6;
  return Math.max(0, Math.min(10, Math.round(valor)));
}

// --- Estado de la demo en memoria (se pierde al recargar) ---

let planGenerado = false;
let inicioTarea: number | null = null;
let fallasPendientes = 1;

const esperar = (ms: number) => new Promise<void>((resolver) => setTimeout(resolver, ms));

export async function listarMisLotesMock(): Promise<LoteResumen[]> {
  await esperar(300);
  return LOTES_DEMO;
}

export async function obtenerUltimoPlanMock(escenario: EscenarioPlan, lote_id: string): Promise<Plan> {
  await esperar(500);
  if (planGenerado || escenario === 'con-plan') return planDemo(lote_id);
  if (escenario === 'error' && fallasPendientes > 0) {
    fallasPendientes--;
    throw { codigo: 'HTTP_500', mensaje: 'No pudimos cargar su plan. Inténtelo de nuevo.' } satisfies ErrorApi;
  }
  if (escenario === 'error') return planDemo(lote_id);
  if (escenario === 'sin-diagnostico') {
    throw { codigo: 'DIAGNOSTICO_NO_DISPONIBLE', mensaje: 'Este lote todavía no tiene diagnóstico.' } satisfies ErrorApi;
  }
  if (escenario === 'calculando') {
    inicioTarea ??= Date.now();
    throw {
      codigo: 'PLAN_EN_CALCULO',
      mensaje: 'Estamos armando el plan de este lote.',
      detalles: [{ campo: 'tarea_id', mensaje: TAREA_DEMO_ID }]
    } satisfies ErrorApi;
  }
  throw { codigo: 'PLAN_NO_DISPONIBLE', mensaje: 'Este lote todavía no tiene plan de siembra.' } satisfies ErrorApi;
}

export async function generarPlanMock(): Promise<IniciarPlanResponse> {
  await esperar(400);
  inicioTarea = Date.now();
  return { tarea_id: TAREA_DEMO_ID };
}

/** La tarea avanza con el tiempo: cada paso dura una cuarta parte de DURACION_TAREA_MS. */
export function tareaPlanDemo(lote: LoteResumen, transcurrido: number): TareaPlanResponse {
  const progreso = Math.min(100, Math.round((transcurrido / DURACION_TAREA_MS) * 100));
  const definicion = [
    { codigo: 'historia', nombre: '40 años de clima de su zona', fuente: 'NASA POWER', resumen: 'Dos temporadas de lluvia al año.' },
    { codigo: 'pronostico', nombre: 'Pronóstico de El Niño y La Niña', fuente: 'NOAA CPC', resumen: 'Se espera un año normal.' },
    { codigo: 'suelo', nombre: 'Cómo es el suelo de su lote', fuente: 'SoilGrids', resumen: 'Suelo suelto que guarda bien el agua.' },
    { codigo: 'rotaciones', nombre: 'Comparando rotaciones de cultivos', fuente: 'Modelo SURCO', resumen: 'Encontramos 3 buenas opciones.' }
  ] as const;
  const pasos = definicion.map((p, i) => {
    const propio = Math.max(0, Math.min(100, Math.round((progreso - i * 25) * 4)));
    return {
      ...p,
      estado: propio >= 100 ? 'lista' : propio > 0 ? 'en_proceso' : 'pendiente',
      progreso: propio,
      resumen: propio >= 100 ? p.resumen : null
    } as const;
  });
  const activo = pasos.find((p) => p.estado === 'en_proceso');
  const lista = progreso >= 100;
  return {
    tarea_id: TAREA_DEMO_ID,
    lote_id: lote.id,
    nombre_lote: lote.nombre,
    area_ha: lote.area_ha,
    corregimiento_nombre: 'Fortalecillas',
    municipio_nombre: 'Neiva',
    poligono: null,
    estado: lista ? 'lista' : 'en_proceso',
    progreso,
    paso_activo_codigo: activo?.codigo ?? null,
    mensaje_estado: lista ? 'Su plan de siembra está listo.' : activo ? `Revisando: ${activo.nombre}…` : 'Empezando…',
    pasos,
    plan_id: lista ? PLAN_DEMO_ID : null
  };
}

export async function obtenerTareaPlanMock(lote_id: string): Promise<TareaPlanResponse> {
  await esperar(250);
  inicioTarea ??= Date.now();
  const tarea = tareaPlanDemo(LOTES_DEMO.find((l) => l.id === lote_id) ?? LOTES_DEMO[0], Date.now() - inicioTarea);
  if (tarea.estado === 'lista') planGenerado = true;
  return tarea;
}

export async function obtenerPlanMock(plan_id: string): Promise<Plan> {
  await esperar(400);
  return { ...planDemo(LOTES_DEMO[0].id), id: plan_id };
}

export async function obtenerLluviasEsperadasMock(): Promise<LluviaMensual[]> {
  await esperar(450);
  return lluviasDemo();
}

export async function obtenerVentanaSiembraMock(cultivo_id: string): Promise<VentanaSiembra> {
  await esperar(450);
  return ventanaDemo(cultivo_id);
}

export async function simularEscenarioMock(cultivo_id: string, delta_lluvia_pct: number, delta_temp_c: number): Promise<ResultadoEscenario> {
  await esperar(350);
  const base = Math.max(...ventanaDemo(cultivo_id).puntos.map((p) => p.frecuencia_exito));
  return { frecuencia_exito: escenarioDemo(base, delta_lluvia_pct, delta_temp_c) };
}

export async function elegirRotacionMock(plan_id: string, rotacion_id: string): Promise<PlanAceptado> {
  await esperar(400);
  return { plan_id, rotacion_id, aceptado_en: new Date().toISOString() };
}
