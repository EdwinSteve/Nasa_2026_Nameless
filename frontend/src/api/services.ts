// src/api/services.ts
// Stubs con datos de ejemplo. Cuando el backend exista, cada función se
// reemplaza por la llamada real al endpoint indicado en su comentario.
import type {
  Tokens,
  Usuario,
  PoliticaVigente,
  RegistroUsuarioPayload,
  MunicipioItem,
  CorregimientoItem,
  CrearFincaPayload,
  FincaResponse,
  CrearLotePayload,
  LoteResponse,
  GuardarPreferenciasPayload,
  IniciarDiagnosticoResponse,
  TareaDiagnosticoResponse
} from './tipos';
import { calcularAreaHa } from '../lib/geo';
import { consultarTareaMock, crearTareaMock, guardarLoteMock } from './mockDiagnostico';

const esperar = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export function guardarTokens(tokens: Tokens): void {
  // Stub listo para almacenamiento seguro
  console.log('[Auth Service] Tokens almacenados. Expira en:', tokens.expira_en);
}

/**
 * GET /politicas/vigente
 * Se invoca al montar el Paso 1
 */
export async function obtenerPoliticaVigente(): Promise<PoliticaVigente> {
  // Stub listo para FastAPI: GET /api/v1/politicas/vigente
  return {
    version: '2026.1',
    url_texto: 'https://surco.ag/politica-datos-ley1581'
  };
}

/**
 * POST /auth/registro
 */
export async function registrarUsuario(
  payload: RegistroUsuarioPayload
): Promise<{ usuario: Usuario; tokens: Tokens }> {
  console.log('[FastAPI] POST /auth/registro:', { ...payload, contrasena: '***' });
  return {
    usuario: {
      id: 'usr_prod_01',
      nombre_completo: payload.nombre_completo,
      celular: payload.celular,
      correo: payload.correo,
      rol: 'productor',
      municipio_residencia: payload.municipio_residencia
    },
    tokens: {
      access_token: 'fake_jwt_access_token_123',
      refresh_token: 'fake_jwt_refresh_token_456',
      token_type: 'bearer',
      expira_en: 900 // 15 minutos exactos según estándar de seguridad
    }
  };
}

/**
 * GET /territorio/municipios?departamento=41
 * DIVIPOLA oficial para el departamento del Huila (código 41)
 */
export async function listarMunicipios(departamento: string = '41'): Promise<MunicipioItem[]> {
  console.log('[FastAPI] GET /territorio/municipios?departamento=' + departamento);
  return [
    { codigo: '41001', nombre: 'Neiva' },
    { codigo: '41013', nombre: 'Agrado' },
    { codigo: '41016', nombre: 'Aipe' },
    { codigo: '41020', nombre: 'Algeciras' },
    { codigo: '41026', nombre: 'Altamira' },
    { codigo: '41132', nombre: 'Campoalegre' },
    { codigo: '41298', nombre: 'Garzón' },
    { codigo: '41349', nombre: 'Hobo' },
    { codigo: '41396', nombre: 'La Plata' },
    { codigo: '41524', nombre: 'Palermo' },
    { codigo: '41548', nombre: 'El Pital' },
    { codigo: '41551', nombre: 'Pitalito' },
    { codigo: '41615', nombre: 'Rivera' },
    { codigo: '41676', nombre: 'Santa María' },
    { codigo: '41872', nombre: 'Villavieja' },
    { codigo: '41885', nombre: 'Yaguará' }
  ];
}

/**
 * GET /territorio/municipios/{municipio}/corregimientos
 */
export async function listarCorregimientos(municipio: string): Promise<CorregimientoItem[]> {
  console.log('[FastAPI] GET /territorio/municipios/' + municipio + '/corregimientos');
  if (municipio === '41001') {
    return [
      { codigo: 'aipecito', nombre: 'Aipecito' },
      { codigo: 'chapinero', nombre: 'Chapinero' },
      { codigo: 'el_caguan', nombre: 'El Caguán' },
      { codigo: 'fortalecillas', nombre: 'Fortalecillas' },
      { codigo: 'guacirco', nombre: 'Guacirco' },
      { codigo: 'rio_ceibas', nombre: 'Río de las Ceibas' },
      { codigo: 'san_luis', nombre: 'San Luis' },
      { codigo: 'vegalarga', nombre: 'Vegalarga' }
    ];
  }
  return [
    { codigo: 'cabecera', nombre: 'Cabecera Municipal' },
    { codigo: 'centro_poblado_1', nombre: 'Centro Poblado Rural 1' }
  ];
}

/**
 * POST /fincas
 */
export async function crearFinca(payload: CrearFincaPayload): Promise<FincaResponse> {
  console.log('[FastAPI] POST /fincas:', payload);
  return {
    id: 'finca_registrada_' + Date.now(),
    nombre: payload.nombre
  };
}

/**
 * POST /fincas/{finca_id}/lotes
 */
export async function crearLote(finca_id: string, payload: CrearLotePayload): Promise<LoteResponse> {
  console.log(`[FastAPI] POST /fincas/${finca_id}/lotes:`, payload);
  const lote: LoteResponse = {
    id: 'lote_registrado_' + Date.now(),
    nombre: payload.nombre,
    area_ha: calcularAreaHa(payload.poligono)
  };
  guardarLoteMock(lote.id, { nombre: lote.nombre, area_ha: lote.area_ha, poligono: payload.poligono });
  return lote;
}

/**
 * PUT /usuarios/me/preferencias
 */
export async function guardarPreferencias(payload: GuardarPreferenciasPayload): Promise<void> {
  console.log('[FastAPI] PUT /usuarios/me/preferencias:', payload);
}

/**
 * POST /lotes/{lote_id}/diagnostico (HTTP 202)
 */
export async function iniciarDiagnostico(lote_id: string): Promise<IniciarDiagnosticoResponse> {
  console.log(`[FastAPI] POST /lotes/${lote_id}/diagnostico`);
  return {
    tarea_id: crearTareaMock(lote_id)
  };
}

/**
 * GET /lotes/{lote_id}/diagnostico/{tarea_id}
 * Se consulta periódicamente hasta que estado sea 'lista' o 'fallida'.
 */
export async function obtenerTareaDiagnostico(
  lote_id: string,
  tarea_id: string
): Promise<TareaDiagnosticoResponse> {
  await esperar(240);
  return consultarTareaMock(lote_id, tarea_id);
}
