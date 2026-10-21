// src/api/tipos.ts
// Contratos con el backend FastAPI (/api/v1).

export interface ErrorDetalle {
  campo: string;
  mensaje: string;
}

export interface ErrorApi {
  codigo: string;
  mensaje: string;
  detalles?: ErrorDetalle[];
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expira_en: number;
}

export interface Usuario {
  id: string;
  nombre_completo: string;
  celular: string;
  correo: string | null;
  rol: 'productor' | 'aprendiz' | 'instructor' | 'admin';
  municipio_residencia: string;
}

export interface PoliticaVigente {
  version: string;
  url_texto: string;
  contenido: string;
}

export interface RegistroUsuarioPayload {
  nombre_completo: string;
  celular: string;
  correo: string | null;
  contrasena: string;
  municipio_residencia: string;
  acepta_politica: true;
  version_politica: string;
}

// Códigos DIVIPOLA del DANE: 5 dígitos el municipio, 8 el centro poblado.
export interface MunicipioItem {
  codigo: string;
  nombre: string;
  lat?: number | null;
  lon?: number | null;
}

export interface CorregimientoItem {
  codigo: string;
  nombre: string;
  tipo?: 'cabecera' | 'centro_poblado';
  lat?: number | null;
  lon?: number | null;
}

export interface CrearFincaPayload {
  nombre: string;
  municipio: string;
  corregimiento: string;
  vereda: string | null;
}

export interface FincaResponse {
  id: string;
  nombre: string;
}

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: number[][][]; // EPSG:4326 [lng, lat]
}

export type TipoRiego = 'gravedad' | 'aspersion' | 'goteo';

export interface CrearLotePayload {
  nombre: string;
  poligono: GeoJSONPolygon;
  tiene_riego: boolean;
  tipo_riego: TipoRiego | null;
  cultivo_anterior: string | null;
}

export interface Coordenada {
  lat: number;
  lon: number;
}

export interface LoteResponse {
  id: string;
  nombre: string;
  area_ha: number;
  centroide: Coordenada; // punto medio del lote, calculado y guardado por el backend
}

export type PrioridadTipo = 'ahorro_agua' | 'ganar_mas' | 'cuidar_suelo' | 'arriesgar_menos';

export interface GuardarPreferenciasPayload {
  orden: PrioridadTipo[];
}

export interface IniciarDiagnosticoResponse {
  tarea_id: string;
}

// --- Diagnóstico satelital del lote ---

// Los cuatro primeros son del diagnóstico; los demás, de la tarea que arma el plan de siembra.
export type CodigoPasoTarea = 'clima' | 'humedad' | 'suelo' | 'verdor' | 'historia' | 'pronostico' | 'rotaciones';
export type EstadoPaso = 'pendiente' | 'en_proceso' | 'lista' | 'fallida';

export interface PasoTarea {
  codigo: CodigoPasoTarea;
  nombre: string;            // Texto legible para el productor
  estado: EstadoPaso;
  progreso: number;          // 0 a 100 individual
  fuente: string;            // Ej: "NASA POWER", "NASA SMAP", "SoilGrids", "NASA HLS"
  resumen: string | null;    // Lo envía el backend al terminar el paso
}

export type EstadoTareaGeneral = 'pendiente' | 'en_proceso' | 'lista' | 'fallida';

export interface TareaDiagnosticoResponse {
  tarea_id: string;
  lote_id: string;
  nombre_lote: string;
  area_ha: number;
  corregimiento_nombre: string;
  municipio_nombre: string;
  poligono: GeoJSONPolygon | null;
  estado: EstadoTareaGeneral;
  progreso: number;          // 0 a 100 general (lo calcula el backend)
  paso_activo_codigo: CodigoPasoTarea | null;
  mensaje_estado: string;    // Frase activa enviada por el backend
  pasos: PasoTarea[];
}

// GET /territorio/elevacion?lat=&lon=
export interface Elevacion {
  altitud_msnm: number;
  fuente: string;
  municipio_codigo: string | null;
  municipio_nombre: string | null;
}

export interface LoginPayload {
  celular: string;
  contrasena: string;
}

// --- Ficha del lote y recomendación de cultivos (modelo predictivo) ---

export interface LoteDetalle {
  id: string;
  nombre: string;
  area_ha: number;
  finca_id: string;
  finca_nombre: string;
  municipio_nombre: string;
  corregimiento_nombre: string;
  poligono: GeoJSONPolygon;
  centroide: Coordenada;
  tiene_riego: boolean;
  tipo_riego: TipoRiego | null;
  cultivo_anterior: string | null;
}

export interface EstadoModelo {
  disponible: boolean;
  corrida: string;
  motivo: string | null;
  ultima_fecha_siembra: string | null;
}

export interface CultivoRecomendado {
  id: string;
  cultivo: string;
  puntaje: number; // 0 a 1
  puntaje_min: number;
  puntaje_max: number;
  prob_exito: number;
  de_cada_10: number;
  riego_neto_mm: number | null;
  riego_bruto_m3_ha: number | null;
  dias_estres: number | null;
  dias_ciclo: number;
}

export interface CultivoDescartado {
  id: string;
  cultivo: string;
  motivo: string;
}

export interface RecomendacionResponse {
  recomendacion_id: string;
  lote_id: string;
  nombre_lote: string;
  fecha_siembra: string;
  estado: 'en_proceso' | 'lista' | 'fallida';
  mensaje: string;
  cultivos: CultivoRecomendado[];
  descartados: CultivoDescartado[];
  contexto: {
    elevacion_m: number;
    ph_0_30: number | null;
    lluvia_90_dias_mm: number | null;
    temperatura_90_dias_c: number | null;
    oni: number | null;
  } | null;
  modelo: string | null;
}

// --- Pantalla Inicio (GET /inicio) ---

/** De dónde sale un dato: va en el chip de fuente ("NASA SMAP · 12 oct"), nunca en el texto principal. */
export interface Procedencia {
  fuente: string;          // "NASA SMAP", "NASA HLS", "NASA POWER"
  fecha: string | null;    // ISO AAAA-MM-DD del dato
}

/** Un indicador del lote en palabras sencillas, con su nivel para el color. */
export interface EstadoSimple {
  nivel: 'bueno' | 'regular' | 'malo' | 'sin_dato';
  etiqueta: string;        // "Bueno", "Normal", "Baja"
  procedencia: Procedencia | null;
}

export type EtapaCultivo = 'siembra' | 'crecimiento' | 'floracion' | 'llenado' | 'cosecha';

export interface ResumenInicio {
  usuario: { nombre: string };
  clima_hoy: {
    temperatura_c: number;
    estado: 'soleado' | 'nublado' | 'lluvia';
    probabilidad_lluvia_pct: number;
    procedencia: Procedencia;
  };
  recomendacion_hoy: {
    tipo: 'riego' | 'siembra' | 'cosecha' | 'alerta' | 'ninguna';
    mensaje: string;
    detalle_porque: string;
    procedencia: Procedencia;
  } | null;
  lote_principal: {
    id: string;
    nombre: string;
    area_ha: number;
    corregimiento_nombre: string;
    altitud_msnm: number | null;
    poligono: GeoJSONPolygon;
    cultivo: {
      nombre: string;
      dia_actual: number;
      dias_ciclo: number;
      etapa_actual: EtapaCultivo;
      fecha_cosecha_estimada: string;
    } | null;
    indicadores: { humedad: EstadoSimple; verdor: EstadoSimple; calor: EstadoSimple };
  } | null;
  alertas_pendientes: number;
  logros: {
    agua_ahorrada_m3: number;
    nitrogeno_kg: number;
    salud_suelo: number;
    salud_suelo_cambio: number;
    frecuencia_exito: number; // 8 = "8 de cada 10 años"
  } | null; // null = usuario nuevo
  series: {
    agua_mensual: Array<{ mes: string; usada_m3_ha: number; recomendada_m3_ha: number }>; // mes AAAA-MM
    salud_suelo: Array<{ mes: string; valor: number }>;
  } | null;
}

/** POST /lotes/{lote_id}/riegos */
export interface RiegoRegistrado {
  riego_id: string;
  lote_id: string;
  registrado_en: string; // ISO con hora
}

// --- Plan de siembra ---

/** GET /lotes: los lotes del usuario, para el selector. */
export interface LoteResumen {
  id: string;
  nombre: string;
  area_ha: number;
}

/** Qué tanto le conviene un cultivo al lote. */
export interface CultivoRanking {
  cultivo_id: string;
  nombre: string;
  ip: number;                    // 0 a 1
  apto: boolean;
  razon_no_apto: string | null;  // "Su zona es muy caliente para el café"
}

export interface Razon {
  texto: string;
  procedencia: Procedencia;
}

export interface Rotacion {
  id: string;
  grado: 'A' | 'B' | 'C' | 'D';
  secuencia: Array<{ cultivo_id: string; nombre: string }>;
  frecuencia_exito: number;      // 8 = "8 de cada 10 años"
  agua_ahorrada_m3: number;
  aporte_nitrogeno: string | null;
  razones: Razon[];
}

/** GET /planes/{id} y GET /lotes/{id}/plan */
export interface Plan {
  id: string;
  lote_id: string;
  calculado_en: string;          // ISO con hora
  rotaciones: Rotacion[];
  ranking: CultivoRanking[];
}

/** GET /lotes/{id}/lluvias-esperadas */
export interface LluviaMensual {
  mes: string;                   // AAAA-MM
  lluvia_mm: number;
  nivel: 'seco' | 'normal' | 'lluvioso';
  nota: string | null;
  procedencia: Procedencia;
}

/** GET /planes/{id}/ventana-siembra?cultivo= */
export interface VentanaSiembra {
  cultivo_id: string;
  puntos: Array<{ fecha: string; frecuencia_exito: number }>;
  mejor_inicio: string;          // AAAA-MM-DD
  mejor_fin: string;
  razones: Razon[];
}

/** POST /lotes/{id}/planes */
export interface IniciarPlanResponse {
  tarea_id: string;
}

/** GET /lotes/{id}/planes/tareas/{tarea_id}: como la del diagnóstico, y al terminar trae el plan. */
export interface TareaPlanResponse extends TareaDiagnosticoResponse {
  plan_id: string | null;
}

/** POST /planes/{id}/escenarios */
export interface ResultadoEscenario {
  frecuencia_exito: number;
}

/** POST /planes/{id}/aceptar */
export interface PlanAceptado {
  plan_id: string;
  rotacion_id: string;
  aceptado_en: string;
}

// --- Asistente SURCO ---

/** Un dato puntual que respalda una respuesta: "Humedad de la tierra: baja". */
export interface TarjetaDato {
  etiqueta: string;
  valor: string;
  unidad: string | null;
  procedencia: Procedencia;
}

/** Un enlace a otra pantalla de la app: "Ver en mi lote". */
export interface EnlaceAccion {
  texto: string;
  ruta: string;
}

export interface MensajeAsistente {
  id: string;
  rol: 'productor' | 'asistente';
  creado_en: string;              // ISO con hora
  texto: string;                  // en una nota de voz, la transcripción
  audio_duracion_s: number | null;
  tarjetas: TarjetaDato[];
  enlaces: EnlaceAccion[];
}

/** GET /asistente/conversaciones?lote_id= */
export interface Conversacion {
  usuario: { nombre: string };
  lote_id: string;
  mensajes: MensajeAsistente[];   // en orden, del más viejo al más nuevo
}

/** POST /asistente/transcripciones */
export interface Transcripcion {
  texto: string;
}

/** GET /lotes/{id}/resumen: lo mismo que lote_principal de GET /inicio, para cualquier lote. */
export type ResumenLote = NonNullable<ResumenInicio['lote_principal']>;
