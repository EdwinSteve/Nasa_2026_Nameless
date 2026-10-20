// src/api/http.ts
// Cliente HTTP de la API de SURCO. Traduce los errores del backend
// ({ code, message, details[{ field, message }] }) al ErrorApi que usa la UI.
import type { ErrorApi, ErrorDetalle, Tokens } from './tipos';
import { cerrarSesionLocal, guardarSesion, obtenerTokens } from './sesion';

// Vacío = mismo origen: Next.js reenvía /api/v1 al backend (ver next.config.ts).
const BASE = (process.env.NEXT_PUBLIC_API_URL ?? '').replace(/\/$/, '') + '/api/v1';

interface ErrorBackend {
  code?: string;
  message?: string;
  details?: { field: string; message: string }[];
}

export interface OpcionesPeticion {
  cuerpo?: unknown;
  /** Agrega el access token y reintenta una vez con el refresh token si expiró. */
  autenticada?: boolean;
  /** Traduce el nombre de un campo del backend al que usa el formulario. */
  campos?: Record<string, string>;
}

const errorDeRed: ErrorApi = {
  codigo: 'RED_SIN_CONEXION',
  mensaje: 'No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.'
};

function aErrorApi(estado: number, cuerpo: ErrorBackend | null, campos: Record<string, string> = {}): ErrorApi {
  const detalles: ErrorDetalle[] = (cuerpo?.details ?? []).map((d) => {
    const campo = d.field.replace(/^body\./, '');
    return { campo: campos[campo] ?? campo, mensaje: d.message.replace(/^Value error, /, '') };
  });
  return {
    codigo: cuerpo?.code ?? `HTTP_${estado}`,
    mensaje: cuerpo?.message ?? 'Ocurrió un error inesperado. Inténtalo de nuevo.',
    ...(detalles.length ? { detalles } : {})
  };
}

async function enviar(metodo: string, ruta: string, opciones: OpcionesPeticion, token?: string): Promise<Response> {
  const cabeceras: Record<string, string> = {};
  if (opciones.cuerpo !== undefined) cabeceras['Content-Type'] = 'application/json';
  if (token) cabeceras.Authorization = `Bearer ${token}`;
  try {
    return await fetch(`${BASE}${ruta}`, {
      method: metodo,
      headers: cabeceras,
      body: opciones.cuerpo === undefined ? undefined : JSON.stringify(opciones.cuerpo)
    });
  } catch {
    throw errorDeRed;
  }
}

// Si varias peticiones encuentran el token vencido a la vez, todas esperan el mismo refresh.
let refrescando: Promise<Tokens | null> | null = null;

async function refrescar(): Promise<Tokens | null> {
  const actuales = obtenerTokens();
  if (!actuales) return null;
  refrescando ??= (async () => {
    const respuesta = await enviar('POST', '/auth/refresh', { cuerpo: { refresh_token: actuales.refresh_token } });
    if (!respuesta.ok) {
      cerrarSesionLocal();
      return null;
    }
    const nuevos = (await respuesta.json()) as Tokens;
    guardarSesion(nuevos);
    return nuevos;
  })().finally(() => {
    refrescando = null;
  });
  return refrescando;
}

export async function peticion<T>(metodo: string, ruta: string, opciones: OpcionesPeticion = {}): Promise<T> {
  let token: string | undefined;
  if (opciones.autenticada) {
    token = obtenerTokens()?.access_token;
    if (!token) throw { codigo: 'AUTH_NO_AUTENTICADO', mensaje: 'Tu sesión terminó. Vuelve a iniciar sesión.' } satisfies ErrorApi;
  }

  let respuesta = await enviar(metodo, ruta, opciones, token);
  if (respuesta.status === 401 && opciones.autenticada) {
    const nuevos = await refrescar();
    if (nuevos) respuesta = await enviar(metodo, ruta, opciones, nuevos.access_token);
  }

  if (respuesta.status === 204) return undefined as T;
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw aErrorApi(respuesta.status, cuerpo as ErrorBackend | null, opciones.campos);
  return cuerpo as T;
}
