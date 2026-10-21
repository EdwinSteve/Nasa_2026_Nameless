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
  ResumenInicio,
  RiegoRegistrado,
  Elevacion,
  LoginPayload,
  LoteResumen,
  Plan,
  LluviaMensual,
  VentanaSiembra,
  IniciarPlanResponse,
  TareaPlanResponse,
  ResultadoEscenario,
  PlanAceptado,
  Conversacion,
  MensajeAsistente,
  Transcripcion,
  ResumenLote
} from './tipos';
import { peticion } from './http';
import { guardarSesion } from './sesion';
import { ESCENARIOS, obtenerResumenInicioMock, registrarRiegoMock, type EscenarioInicio } from './mocks/inicio';
import * as mockPlan from './mocks/plan';
import * as mockAsistente from './mocks/asistente';

// --- Interruptor de mocks ---
// NEXT_PUBLIC_USAR_MOCKS="inicio" (o "inicio:nuevo") activa el mock SOLO de los endpoints de la
// pantalla Inicio, que el backend todavía no tiene. El resto sigue contra la API real.
// ?demo=historia | nuevo | sin-lote en la URL cambia el escenario sin reiniciar.
const MOCKS = (process.env.NEXT_PUBLIC_USAR_MOCKS ?? '')
  .split(',')
  .map((m) => m.trim())
  .filter(Boolean);

/** El escenario de demo de un grupo de mocks ("inicio", "plan"), o null si ese grupo va contra la API. */
function escenarioMock<T extends string>(grupo: string, escenarios: readonly T[], porDefecto: T): T | null {
  const activo = MOCKS.find((m) => m === grupo || m.startsWith(`${grupo}:`));
  if (!activo) return null;
  const desdeUrl = typeof window === 'undefined' ? null : new URLSearchParams(window.location.search).get('demo');
  const elegido = [desdeUrl, activo.split(':')[1]].find((e): e is T => (escenarios as readonly (string | null | undefined)[]).includes(e));
  return elegido ?? porDefecto;
}

const mockInicio = (): EscenarioInicio | null => escenarioMock('inicio', ESCENARIOS, 'historia');
// "plan" (o "plan:sin-plan"...) simula los endpoints del plan de siembra; ?demo=con-plan | sin-plan |
// sin-diagnostico | calculando | error cambia el escenario.
const mockDePlan = (): mockPlan.EscenarioPlan | null => escenarioMock('plan', mockPlan.ESCENARIOS_PLAN, 'con-plan');
// "asistente" simula el chat; ?demo=con-historia | nuevo | falla-envio cambia el escenario.
const mockDeAsistente = (): mockAsistente.EscenarioAsistente | null =>
  escenarioMock('asistente', mockAsistente.ESCENARIOS_ASISTENTE, 'con-historia');

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

/** GET /inicio: todo lo que muestra la pantalla Inicio. Pendiente en el backend (PENDIENTES-BACKEND.md). */
export async function obtenerResumenInicio(): Promise<ResumenInicio> {
  const escenario = mockInicio();
  if (escenario) return obtenerResumenInicioMock(escenario);
  return peticion<ResumenInicio>('GET', '/inicio', { autenticada: true });
}

/** POST /lotes/{lote_id}/riegos: el productor avisa que ya regó. Pendiente en el backend. */
export async function registrarRiego(lote_id: string): Promise<RiegoRegistrado> {
  if (mockInicio()) return registrarRiegoMock(lote_id);
  return peticion<RiegoRegistrado>('POST', `/lotes/${encodeURIComponent(lote_id)}/riegos`, {
    cuerpo: {},
    autenticada: true
  });
}

// --- Plan de siembra (pendientes en el backend: ver PENDIENTES-BACKEND.md) ---

const lote = (id: string) => `/lotes/${encodeURIComponent(id)}`;
const plan = (id: string) => `/planes/${encodeURIComponent(id)}`;

/** GET /lotes: los lotes del usuario. Lo usan el Plan y el Asistente: se simula con cualquiera de los dos. */
export async function listarMisLotes(): Promise<LoteResumen[]> {
  if (mockDePlan() || mockDeAsistente()) return mockPlan.listarMisLotesMock();
  return peticion<LoteResumen[]>('GET', '/lotes', { autenticada: true });
}

/** POST /lotes/{id}/planes (HTTP 202): empieza a armar el plan; se sigue con obtenerTareaPlan. */
export async function generarPlan(lote_id: string): Promise<IniciarPlanResponse> {
  if (mockDePlan()) return mockPlan.generarPlanMock();
  return peticion<IniciarPlanResponse>('POST', `${lote(lote_id)}/planes`, { cuerpo: {}, autenticada: true });
}

/** GET /lotes/{id}/planes/tareas/{tarea_id}: avance de la tarea; al terminar trae plan_id. */
export async function obtenerTareaPlan(lote_id: string, tarea_id: string): Promise<TareaPlanResponse> {
  if (mockDePlan()) return mockPlan.obtenerTareaPlanMock(lote_id);
  return peticion<TareaPlanResponse>('GET', `${lote(lote_id)}/planes/tareas/${encodeURIComponent(tarea_id)}`, { autenticada: true });
}

/** GET /planes/{id} */
export async function obtenerPlan(plan_id: string): Promise<Plan> {
  if (mockDePlan()) return mockPlan.obtenerPlanMock(plan_id);
  return peticion<Plan>('GET', plan(plan_id), { autenticada: true });
}

/**
 * GET /lotes/{id}/plan: el último plan del lote.
 * Errores: 404 PLAN_NO_DISPONIBLE, 409 DIAGNOSTICO_NO_DISPONIBLE y 409 PLAN_EN_CALCULO (con tarea_id en detalles).
 */
export async function obtenerUltimoPlan(lote_id: string): Promise<Plan> {
  const escenario = mockDePlan();
  if (escenario) return mockPlan.obtenerUltimoPlanMock(escenario, lote_id);
  return peticion<Plan>('GET', `${lote(lote_id)}/plan`, { autenticada: true });
}

/** GET /lotes/{id}/lluvias-esperadas: mes a mes, desde el actual. */
export async function obtenerLluviasEsperadas(lote_id: string): Promise<LluviaMensual[]> {
  if (mockDePlan()) return mockPlan.obtenerLluviasEsperadasMock();
  return peticion<LluviaMensual[]>('GET', `${lote(lote_id)}/lluvias-esperadas`, { autenticada: true });
}

/** GET /planes/{id}/ventana-siembra?cultivo= */
export async function obtenerVentanaSiembra(plan_id: string, cultivo_id: string): Promise<VentanaSiembra> {
  if (mockDePlan()) return mockPlan.obtenerVentanaSiembraMock(cultivo_id);
  return peticion<VentanaSiembra>('GET', `${plan(plan_id)}/ventana-siembra?cultivo=${encodeURIComponent(cultivo_id)}`, {
    autenticada: true
  });
}

/** POST /planes/{id}/escenarios: cuántos años de cada 10 le iría bien si cambia el clima. */
export async function simularEscenario(
  plan_id: string,
  cultivo_id: string,
  delta_lluvia_pct: number,
  delta_temp_c: number
): Promise<ResultadoEscenario> {
  if (mockDePlan()) return mockPlan.simularEscenarioMock(cultivo_id, delta_lluvia_pct, delta_temp_c);
  return peticion<ResultadoEscenario>('POST', `${plan(plan_id)}/escenarios`, {
    cuerpo: { cultivo_id, delta_lluvia_pct, delta_temp_c },
    autenticada: true
  });
}

/** POST /planes/{id}/aceptar: el productor elige una rotación. */
export async function elegirRotacion(plan_id: string, rotacion_id: string): Promise<PlanAceptado> {
  if (mockDePlan()) return mockPlan.elegirRotacionMock(plan_id, rotacion_id);
  return peticion<PlanAceptado>('POST', `${plan(plan_id)}/aceptar`, { cuerpo: { rotacion_id }, autenticada: true });
}

// --- Asistente SURCO (pendientes en el backend: ver PENDIENTES-BACKEND.md) ---

/** GET /asistente/conversaciones?lote_id=: el nombre del usuario y los mensajes con ese lote. */
export async function obtenerConversacion(lote_id: string): Promise<Conversacion> {
  const escenario = mockDeAsistente();
  if (escenario) return mockAsistente.obtenerConversacionMock(escenario, lote_id);
  return peticion<Conversacion>('GET', `/asistente/conversaciones?lote_id=${encodeURIComponent(lote_id)}`, { autenticada: true });
}

/**
 * POST /asistente/mensajes: la pregunta del productor; responde con el mensaje del asistente.
 * audio_duracion_s va cuando la pregunta fue una nota de voz (texto = transcripción).
 */
export async function enviarMensaje(lote_id: string, texto: string, audio_duracion_s: number | null = null): Promise<MensajeAsistente> {
  const escenario = mockDeAsistente();
  if (escenario) return mockAsistente.enviarMensajeMock(escenario, lote_id, texto);
  return peticion<MensajeAsistente>('POST', '/asistente/mensajes', {
    cuerpo: { lote_id, texto, audio_duracion_s },
    autenticada: true
  });
}

/** POST /asistente/transcripciones (multipart, campo "audio"): la nota de voz en texto. */
export async function transcribirAudio(audio: Blob): Promise<Transcripcion> {
  if (mockDeAsistente()) return mockAsistente.transcribirAudioMock();
  const formulario = new FormData();
  formulario.append('audio', audio, `nota.${audio.type.includes('mp4') ? 'm4a' : 'webm'}`);
  return peticion<Transcripcion>('POST', '/asistente/transcripciones', { cuerpo: formulario, autenticada: true });
}

/** POST /asistente/mensajes/{id}/valoracion: "Me sirvió" / "No me sirvió". */
export async function valorarMensaje(mensaje_id: string, util: boolean): Promise<void> {
  if (mockDeAsistente()) return mockAsistente.valorarMensajeMock();
  await peticion<void>('POST', `/asistente/mensajes/${encodeURIComponent(mensaje_id)}/valoracion`, {
    cuerpo: { util },
    autenticada: true
  });
}

/** GET /lotes/{id}/resumen: cultivo, etapa e indicadores del lote (panel del asistente en escritorio). */
export async function obtenerResumenLote(lote_id: string): Promise<ResumenLote> {
  if (mockDeAsistente()) return mockAsistente.obtenerResumenLoteMock(lote_id);
  return peticion<ResumenLote>('GET', `/lotes/${encodeURIComponent(lote_id)}/resumen`, { autenticada: true });
}
