// src/api/mockDiagnostico.ts
// Simulación en memoria del backend de diagnóstico. Solo la usa services.ts;
// los componentes nunca la importan. Se borra cuando exista el endpoint real.
import type { GeoJSONPolygon, PasoTarea, TareaDiagnosticoResponse } from './tipos';

interface LoteMock {
  nombre: string;
  area_ha: number;
  poligono: GeoJSONPolygon;
}

const LOTE_DEMO: LoteMock = {
  nombre: 'Lote La Esperanza',
  area_ha: 6.4,
  poligono: {
    type: 'Polygon',
    coordinates: [[
      [-75.2941, 2.9912],
      [-75.2895, 2.992],
      [-75.2882, 2.9865],
      [-75.293, 2.9858],
      [-75.2941, 2.9912]
    ]]
  }
};

// Ubicación fija mientras el mock no conozca la finca real
const UBICACION_DEMO = { corregimiento_nombre: 'Fortalecillas', municipio_nombre: 'Neiva' };

// Velocidad por fuente: NASA POWER es rápido, HLS es el más lento
const INCREMENTO_POR_PASO: Record<PasoTarea['codigo'], number> = {
  clima: 25,
  humedad: 18,
  suelo: 14,
  verdor: 12
};

const RESUMEN_POR_PASO: Record<PasoTarea['codigo'], string> = {
  clima: 'Histórico 40 años: 1.340 mm/año y 27 °C promedio',
  humedad: '31% en capa arable: retención adecuada para siembra',
  suelo: 'Franco-arcilloso, pH 6.2, pendiente moderada (14%)',
  verdor: 'Vigor vegetativo óptimo detectado (NDVI 0.68)'
};

const FRASE_POR_PASO: Record<PasoTarea['codigo'], string> = {
  clima: 'Revisando 40 años de clima de tu zona...',
  humedad: 'Midiendo la humedad de la tierra con el satélite SMAP...',
  suelo: 'Leyendo el tipo de suelo y la pendiente con SoilGrids...',
  verdor: 'Mirando el verdor del terreno desde el espacio...'
};

const lotes = new Map<string, LoteMock>();
const tareas = new Map<string, TareaDiagnosticoResponse>();

export function guardarLoteMock(loteId: string, lote: LoteMock): void {
  lotes.set(loteId, lote);
}

function crearEstadoInicial(loteId: string, tareaId: string): TareaDiagnosticoResponse {
  const lote = lotes.get(loteId) ?? LOTE_DEMO;
  return {
    tarea_id: tareaId,
    lote_id: loteId,
    nombre_lote: lote.nombre,
    area_ha: lote.area_ha,
    poligono: lote.poligono,
    ...UBICACION_DEMO,
    estado: 'en_proceso',
    progreso: 5,
    paso_activo_codigo: 'clima',
    mensaje_estado: 'Conectando con satélites para analizar tu lote...',
    pasos: [
      { codigo: 'clima', nombre: 'Clima de los últimos 40 años', estado: 'en_proceso', progreso: 20, fuente: 'NASA POWER', resumen: null },
      { codigo: 'humedad', nombre: 'Humedad de la tierra', estado: 'pendiente', progreso: 0, fuente: 'NASA SMAP', resumen: null },
      { codigo: 'suelo', nombre: 'Tipo de suelo y pendiente', estado: 'pendiente', progreso: 0, fuente: 'SoilGrids', resumen: null },
      { codigo: 'verdor', nombre: 'Verdor del terreno', estado: 'pendiente', progreso: 0, fuente: 'NASA HLS', resumen: null }
    ]
  };
}

/** Función pura: devuelve el siguiente estado de la tarea. */
export function simularAvanceTarea(previo: TareaDiagnosticoResponse): TareaDiagnosticoResponse {
  if (previo.estado === 'lista' || previo.estado === 'fallida') return previo;

  const pasos: PasoTarea[] = previo.pasos.map((p) => {
    if (p.estado === 'lista' || p.estado === 'fallida') return p;
    const progreso = Math.min(100, p.progreso + INCREMENTO_POR_PASO[p.codigo]);
    return progreso >= 100
      ? { ...p, progreso, estado: 'lista', resumen: RESUMEN_POR_PASO[p.codigo] }
      : { ...p, progreso, estado: 'en_proceso' };
  });

  const progreso = Math.round(pasos.reduce((suma, p) => suma + p.progreso, 0) / pasos.length);
  const todosListos = pasos.every((p) => p.estado === 'lista');
  const pasoActivo = pasos.find((p) => p.estado === 'en_proceso') ?? null;

  return {
    ...previo,
    progreso,
    estado: todosListos ? 'lista' : 'en_proceso',
    paso_activo_codigo: pasoActivo?.codigo ?? null,
    mensaje_estado: todosListos
      ? '¡Diagnóstico completo! Ya puedes ver tu lote.'
      : pasoActivo
        ? FRASE_POR_PASO[pasoActivo.codigo]
        : previo.mensaje_estado,
    pasos
  };
}

export function crearTareaMock(loteId: string): string {
  const tareaId = `task_diag_${loteId}`;
  tareas.set(tareaId, crearEstadoInicial(loteId, tareaId));
  return tareaId;
}

/**
 * Cada consulta avanza la tarea un paso. Si la tarea no existe (p. ej. se
 * recargó la página y se perdió la memoria), se crea una de demostración.
 */
export function consultarTareaMock(loteId: string, tareaId: string): TareaDiagnosticoResponse {
  const actual = tareas.get(tareaId);
  if (!actual) {
    const inicial = crearEstadoInicial(loteId, tareaId);
    tareas.set(tareaId, inicial);
    return inicial;
  }
  const siguiente = simularAvanceTarea(actual);
  tareas.set(tareaId, siguiente);
  return siguiente;
}
