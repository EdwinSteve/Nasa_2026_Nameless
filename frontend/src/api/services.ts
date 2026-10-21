// src/api/services.ts
// Una función por endpoint de la API (/api/v1). Los componentes solo usan estas
// funciones y los tipos de tipos.ts; los detalles de cada contrato quedan aquí.
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
  TareaDiagnosticoResponse,
  LoteDetalle,
  EstadoModelo,
  RecomendacionResponse,
  Elevacion,
  LoginPayload
} from './tipos';
import { peticion } from './http';
import { guardarSesion } from './sesion';

export function guardarTokens(tokens: Tokens): void {
  guardarSesion(tokens);
}

/** GET /politicas/vigente: se invoca al montar el paso 1. */
export async function obtenerPoliticaVigente(): Promise<PoliticaVigente> {
  return peticion<PoliticaVigente>('GET', '/politicas/vigente');
}

/** POST /auth/login: inicia sesión con celular y contraseña y guarda los tokens. */
export async function iniciarSesion(payload: LoginPayload): Promise<Tokens> {
  const tokens = await peticion<Tokens>('POST', '/auth/login', { cuerpo: payload });
  guardarSesion(tokens);
  return tokens;
}

// El módulo identidad usa nombres en inglés para el registro: se traducen aquí.
interface RegistroBackend {
  user: {
    id: string;
    full_name: string | null;
    phone: string;
    role: Usuario['rol'];
    municipality: string | null;
  };
  tokens: { access_token: string; refresh_token: string; token_type: 'bearer'; expires_in: number };
}

const CAMPOS_REGISTRO: Record<string, string> = {
  full_name: 'nombre_completo',
  phone: 'celular',
  email: 'correo',
  password: 'contrasena',
  municipality: 'municipio_residencia',
  accepts_policy: 'acepta_politica',
  policy_version: 'version_politica'
};

/** POST /auth/registro: crea la cuenta y deja la sesión iniciada. */
export async function registrarUsuario(
  payload: RegistroUsuarioPayload
): Promise<{ usuario: Usuario; tokens: Tokens }> {
  const r = await peticion<RegistroBackend>('POST', '/auth/registro', {
    cuerpo: {
      full_name: payload.nombre_completo,
      phone: payload.celular,
      email: payload.correo,
      password: payload.contrasena,
      municipality: payload.municipio_residencia,
      district: null,
      accepts_policy: payload.acepta_politica,
      policy_version: payload.version_politica
    },
    campos: CAMPOS_REGISTRO
  });
  return {
    usuario: {
      id: r.user.id,
      nombre_completo: r.user.full_name ?? payload.nombre_completo,
      celular: r.user.phone,
      correo: payload.correo,
      rol: r.user.role,
      municipio_residencia: r.user.municipality ?? payload.municipio_residencia
    },
    tokens: {
      access_token: r.tokens.access_token,
      refresh_token: r.tokens.refresh_token,
      token_type: r.tokens.token_type,
      expira_en: r.tokens.expires_in
    }
  };
}

/** GET /territorio/municipios?departamento=41: DIVIPOLA del Huila. */
export async function listarMunicipios(departamento: string = '41'): Promise<MunicipioItem[]> {
  return peticion<MunicipioItem[]>('GET', `/territorio/municipios?departamento=${encodeURIComponent(departamento)}`);
}

/** GET /territorio/municipios/{municipio}/corregimientos: casco urbano y centros poblados. */
export async function listarCorregimientos(municipio: string): Promise<CorregimientoItem[]> {
  return peticion<CorregimientoItem[]>('GET', `/territorio/municipios/${encodeURIComponent(municipio)}/corregimientos`);
}

/** GET /territorio/elevacion?lat=&lon=: altitud del punto según el modelo de elevación. */
export async function obtenerElevacion(lat: number, lon: number): Promise<Elevacion> {
  const consulta = new URLSearchParams({ lat: String(lat), lon: String(lon) });
  return peticion<Elevacion>('GET', `/territorio/elevacion?${consulta.toString()}`);
}

/** POST /fincas */
export async function crearFinca(payload: CrearFincaPayload): Promise<FincaResponse> {
  return peticion<FincaResponse>('POST', '/fincas', { cuerpo: payload, autenticada: true });
}

/** POST /fincas/{finca_id}/lotes: el área oficial la calcula el servidor. */
export async function crearLote(finca_id: string, payload: CrearLotePayload): Promise<LoteResponse> {
  return peticion<LoteResponse>('POST', `/fincas/${encodeURIComponent(finca_id)}/lotes`, {
    cuerpo: payload,
    autenticada: true
  });
}

/** PUT /usuarios/me/preferencias */
export async function guardarPreferencias(payload: GuardarPreferenciasPayload): Promise<void> {
  await peticion<void>('PUT', '/usuarios/me/preferencias', { cuerpo: payload, autenticada: true });
}

/** POST /lotes/{lote_id}/diagnostico (HTTP 202) */
export async function iniciarDiagnostico(lote_id: string): Promise<IniciarDiagnosticoResponse> {
  return peticion<IniciarDiagnosticoResponse>('POST', `/lotes/${encodeURIComponent(lote_id)}/diagnostico`, {
    autenticada: true
  });
}

/**
 * GET /lotes/{lote_id}/diagnostico/{tarea_id}
 * Se consulta periódicamente hasta que estado sea 'lista' o 'fallida'.
 */
export async function obtenerTareaDiagnostico(
  lote_id: string,
  tarea_id: string
): Promise<TareaDiagnosticoResponse> {
  return peticion<TareaDiagnosticoResponse>(
    'GET',
    `/lotes/${encodeURIComponent(lote_id)}/diagnostico/${encodeURIComponent(tarea_id)}`,
    { autenticada: true }
  );
}

/** GET /lotes/{lote_id}: detalle del lote del productor. */
export async function obtenerLote(lote_id: string): Promise<LoteDetalle> {
  return peticion<LoteDetalle>('GET', `/lotes/${encodeURIComponent(lote_id)}`, { autenticada: true });
}

/** GET /recomendaciones/modelo: si el servidor tiene el modelo predictivo. */
export async function obtenerEstadoModelo(): Promise<EstadoModelo> {
  return peticion<EstadoModelo>('GET', '/recomendaciones/modelo');
}

/** POST /lotes/{lote_id}/recomendaciones (HTTP 202). Sin fecha: "si siembras ahora". */
export async function solicitarRecomendacion(
  lote_id: string,
  fecha_siembra?: string
): Promise<{ recomendacion_id: string; fecha_siembra: string }> {
  return peticion('POST', `/lotes/${encodeURIComponent(lote_id)}/recomendaciones`, {
    cuerpo: fecha_siembra ? { fecha_siembra } : {},
    autenticada: true
  });
}

/** GET /lotes/{lote_id}/recomendaciones/{id}: se consulta hasta que esté 'lista' o 'fallida'. */
export async function obtenerRecomendacion(lote_id: string, recomendacion_id: string): Promise<RecomendacionResponse> {
  return peticion<RecomendacionResponse>(
    'GET',
    `/lotes/${encodeURIComponent(lote_id)}/recomendaciones/${encodeURIComponent(recomendacion_id)}`,
    { autenticada: true }
  );
}
