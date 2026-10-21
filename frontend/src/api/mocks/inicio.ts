// src/api/mocks/inicio.ts
// Datos de demostración de GET /inicio y POST /lotes/{id}/riegos mientras el backend no los tenga.
// Solo los usa services.ts cuando NEXT_PUBLIC_USAR_MOCKS incluye "inicio" (ver PENDIENTES-BACKEND.md).
// Las fechas y los meses se calculan a partir de hoy: nada queda fijo.
import type { GeoJSONPolygon, ResumenInicio, RiegoRegistrado } from '../tipos';

export type EscenarioInicio = 'historia' | 'nuevo' | 'sin-lote';
export const ESCENARIOS: readonly EscenarioInicio[] = ['historia', 'nuevo', 'sin-lote'];

const POLIGONO_DEMO: GeoJSONPolygon = {
  type: 'Polygon',
  coordinates: [[
    [-75.2941, 2.9912],
    [-75.2895, 2.992],
    [-75.2882, 2.9865],
    [-75.293, 2.9858],
    [-75.2941, 2.9912]
  ]]
};

/** AAAA-MM-DD en la hora local: toISOString usaría UTC y en la noche de Colombia daría mañana. */
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

/** Los últimos n meses terminando en el actual, como "AAAA-MM". */
export function ultimosMeses(n: number, hoy: Date): string[] {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(hoy.getFullYear(), hoy.getMonth() - (n - 1 - i), 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  });
}

export function resumenDemo(escenario: EscenarioInicio, hoy: Date = new Date()): ResumenInicio {
  const hace2Dias = isoDia(sumarDias(hoy, -2));
  const clima: ResumenInicio['clima_hoy'] = {
    temperatura_c: 31,
    estado: 'soleado',
    probabilidad_lluvia_pct: 10,
    procedencia: { fuente: 'NASA POWER', fecha: isoDia(hoy) }
  };

  if (escenario === 'sin-lote') {
    return {
      usuario: { nombre: 'Ana' },
      clima_hoy: clima,
      recomendacion_hoy: null,
      lote_principal: null,
      alertas_pendientes: 0,
      logros: null,
      series: null
    };
  }

  const sinDato = { nivel: 'sin_dato', etiqueta: 'Sin dato aún', procedencia: null } as const;

  if (escenario === 'nuevo') {
    return {
      usuario: { nombre: 'Ana' },
      clima_hoy: clima,
      recomendacion_hoy: null,
      lote_principal: {
        id: 'lote-demo-nuevo',
        nombre: 'La Vega',
        area_ha: 6.4,
        corregimiento_nombre: 'Fortalecillas',
        altitud_msnm: 442,
        poligono: POLIGONO_DEMO,
        cultivo: null,
        indicadores: {
          humedad: { nivel: 'malo', etiqueta: 'Baja', procedencia: { fuente: 'NASA SMAP', fecha: hace2Dias } },
          verdor: { ...sinDato },
          calor: { nivel: 'bueno', etiqueta: 'Normal', procedencia: { fuente: 'NASA POWER', fecha: isoDia(hoy) } }
        }
      },
      alertas_pendientes: 1,
      logros: null,
      series: null
    };
  }

  const meses12 = ultimosMeses(12, hoy);
  const salud = [63, 63, 64, 65, 65, 66, 67, 68, 69, 70, 71, 72];
  const usada = [510, 480, 430, 390, 420, 360];
  const recomendada = [450, 430, 410, 380, 400, 390];
  return {
    usuario: { nombre: 'Ernesto' },
    clima_hoy: clima,
    recomendacion_hoy: {
      tipo: 'riego',
      mensaje: 'Riega tu maíz esta semana: unos 450 m³ por hectárea. La tierra está más seca de lo normal.',
      detalle_porque:
        'La humedad en la zona de las raíces está en 12 %, por debajo de lo que el maíz necesita en la floración. ' +
        'Con el calor de estos días el cultivo pierde unos 5 mm de agua al día, y no se espera lluvia en la semana.',
      procedencia: { fuente: 'NASA SMAP', fecha: hace2Dias }
    },
    lote_principal: {
      id: 'lote-demo-historia',
      nombre: 'La Vega',
      area_ha: 6.4,
      corregimiento_nombre: 'Fortalecillas',
      altitud_msnm: 442,
      poligono: POLIGONO_DEMO,
      cultivo: {
        nombre: 'Maíz',
        dia_actual: 54,
        dias_ciclo: 120,
        etapa_actual: 'floracion',
        fecha_cosecha_estimada: isoDia(sumarDias(hoy, 120 - 54))
      },
      indicadores: {
        humedad: { nivel: 'malo', etiqueta: 'Baja', procedencia: { fuente: 'NASA SMAP', fecha: hace2Dias } },
        verdor: { nivel: 'bueno', etiqueta: 'Bueno', procedencia: { fuente: 'NASA HLS', fecha: isoDia(sumarDias(hoy, -5)) } },
        calor: { nivel: 'bueno', etiqueta: 'Normal', procedencia: { fuente: 'NASA POWER', fecha: isoDia(hoy) } }
      }
    },
    alertas_pendientes: 2,
    logros: { agua_ahorrada_m3: 1840, nitrogeno_kg: 48, salud_suelo: 72, salud_suelo_cambio: 9, frecuencia_exito: 8 },
    series: {
      agua_mensual: meses12.slice(-6).map((mes, i) => ({ mes, usada_m3_ha: usada[i], recomendada_m3_ha: recomendada[i] })),
      salud_suelo: meses12.map((mes, i) => ({ mes, valor: salud[i] }))
    }
  };
}

const esperar = (ms: number) => new Promise<void>((resolver) => setTimeout(resolver, ms));

export async function obtenerResumenInicioMock(escenario: EscenarioInicio): Promise<ResumenInicio> {
  await esperar(500);
  return resumenDemo(escenario);
}

export async function registrarRiegoMock(lote_id: string): Promise<RiegoRegistrado> {
  await esperar(400);
  return { riego_id: `riego-demo-${Date.now()}`, lote_id, registrado_en: new Date().toISOString() };
}
