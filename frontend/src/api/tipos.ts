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
  rol: 'productor' | 'tecnico' | 'admin';
  municipio_residencia: string;
}

export interface PoliticaVigente {
  version: string;
  url_texto: string;
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

export interface MunicipioItem {
  codigo: string;
  nombre: string;
}

export interface CorregimientoItem {
  codigo: string;
  nombre: string;
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

export interface LoteResponse {
  id: string;
  nombre: string;
  area_ha: number;
}

export type PrioridadTipo = 'ahorro_agua' | 'ganar_mas' | 'cuidar_suelo' | 'arriesgar_menos';

export interface GuardarPreferenciasPayload {
  orden: PrioridadTipo[];
}

export interface IniciarDiagnosticoResponse {
  tarea_id: string;
}

// --- Diagnóstico satelital del lote ---

export type CodigoPasoTarea = 'clima' | 'humedad' | 'suelo' | 'verdor';
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
