// src/api/sesion.ts
// Tokens de la sesión. El access token vive en memoria y se copia en localStorage
// junto con el refresh token para sobrevivir a una recarga.
// Pendiente de seguridad: pasar el refresh token a una cookie httpOnly cuando el
// backend la emita; en localStorage queda expuesto a un XSS.
import type { Tokens } from './tipos';

const CLAVE = 'surco.sesion';

let enMemoria: Tokens | null = null;

function leerAlmacenado(): Tokens | null {
  try {
    const texto = window.localStorage.getItem(CLAVE);
    return texto ? (JSON.parse(texto) as Tokens) : null;
  } catch {
    return null;
  }
}

export function obtenerTokens(): Tokens | null {
  if (enMemoria) return enMemoria;
  if (typeof window === 'undefined') return null;
  enMemoria = leerAlmacenado();
  return enMemoria;
}

export function guardarSesion(tokens: Tokens): void {
  enMemoria = tokens;
  try {
    window.localStorage.setItem(CLAVE, JSON.stringify(tokens));
  } catch {
    // Navegación privada o almacenamiento bloqueado: la sesión dura lo que dure la pestaña
  }
}

export function cerrarSesionLocal(): void {
  enMemoria = null;
  try {
    window.localStorage.removeItem(CLAVE);
  } catch {
    // nada que limpiar
  }
}
