// src/hooks/useAutoScroll.ts
// Baja al último mensaje cuando llega uno nuevo, pero solo si el usuario ya estaba abajo.
// Si estaba leyendo más arriba no lo mueve: avisa que hay mensajes nuevos.
'use client';

import { useCallback, useEffect, useLayoutEffect, useRef, useState, type RefObject } from 'react';

/** A menos de esto del final se considera que el usuario "está abajo". */
export const MARGEN_FINAL_PX = 120;

export function estaCercaDelFinal(el: Pick<HTMLElement, 'scrollHeight' | 'scrollTop' | 'clientHeight'>): boolean {
  return el.scrollHeight - el.scrollTop - el.clientHeight < MARGEN_FINAL_PX;
}

const reducirMovimiento = () =>
  typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export interface UseAutoScroll {
  contenedor: RefObject<HTMLDivElement | null>;
  hayNuevos: boolean;
  irAlFinal: () => void;
  alDesplazar: () => void;
}

/** `version` cambia cada vez que llega contenido nuevo al final (mensajes, "pensando"). */
export function useAutoScroll(version: string): UseAutoScroll {
  const contenedor = useRef<HTMLDivElement | null>(null);
  const cerca = useRef(true);
  const primera = useRef(true);
  const [hayNuevos, setHayNuevos] = useState(false);

  const irAlFinal = useCallback(() => {
    const el = contenedor.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: reducirMovimiento() ? 'auto' : 'smooth' });
    cerca.current = true;
    setHayNuevos(false);
  }, []);

  const alDesplazar = useCallback(() => {
    const el = contenedor.current;
    if (!el) return;
    cerca.current = estaCercaDelFinal(el);
    if (cerca.current) setHayNuevos(false);
  }, []);

  useLayoutEffect(() => {
    const el = contenedor.current;
    if (!el) return;
    if (primera.current) {
      // Al abrir la conversación se arranca abajo, sin animación
      primera.current = false;
      el.scrollTop = el.scrollHeight;
      return;
    }
    if (cerca.current) irAlFinal();
    else setHayNuevos(true);
  }, [version, irAlFinal]);

  // Si el contenedor cambia de alto (teclado del celular, ventana) y el usuario estaba abajo, sigue abajo
  useEffect(() => {
    const el = contenedor.current;
    if (!el || typeof ResizeObserver === 'undefined') return;
    const observador = new ResizeObserver(() => {
      if (cerca.current) el.scrollTop = el.scrollHeight;
    });
    observador.observe(el);
    return () => observador.disconnect();
  }, []);

  return { contenedor, hayNuevos, irAlFinal, alDesplazar };
}
