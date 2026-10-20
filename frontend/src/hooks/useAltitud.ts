'use client';

// Altitud del lugar donde está el productor. Nunca pide la ubicación al cargar:
// solo si el permiso ya estaba concedido o cuando el usuario toca el chip.
import { useCallback, useEffect, useRef, useState } from 'react';
import type { Elevacion } from '../api/tipos';
import { obtenerElevacion } from '../api/services';

export type EstadoAltitud = 'sin_permiso' | 'cargando' | 'con_dato' | 'no_disponible';

const OPCIONES_GPS: PositionOptions = { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 };
const numeroCO = new Intl.NumberFormat('es-CO');

export function useAltitud() {
  const [estado, setEstado] = useState<EstadoAltitud>('sin_permiso');
  const [elevacion, setElevacion] = useState<Elevacion | null>(null);
  const montado = useRef(true);
  const enCurso = useRef(false);

  const leerUbicacion = useCallback(() => {
    if (enCurso.current) return;
    if (!('geolocation' in navigator)) {
      setEstado('no_disponible');
      return;
    }
    enCurso.current = true;
    setEstado('cargando');
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          // La altitud siempre viene del backend (modelo de elevación), no de coords.altitude
          const dato = await obtenerElevacion(coords.latitude, coords.longitude);
          if (!montado.current) return;
          setElevacion(dato);
          setEstado('con_dato');
        } catch {
          if (montado.current) setEstado('no_disponible');
        } finally {
          enCurso.current = false;
        }
      },
      () => {
        enCurso.current = false;
        if (montado.current) setEstado('no_disponible');
      },
      OPCIONES_GPS,
    );
  }, []);

  useEffect(() => {
    montado.current = true;
    if ('permissions' in navigator && 'geolocation' in navigator) {
      navigator.permissions
        .query({ name: 'geolocation' })
        .then((permiso) => {
          if (!montado.current) return;
          if (permiso.state === 'granted') leerUbicacion();
          else if (permiso.state === 'denied') setEstado('no_disponible');
        })
        .catch(() => undefined); // Si el navegador no lo soporta, queda en 'sin_permiso'
    }
    return () => {
      montado.current = false;
    };
  }, [leerUbicacion]);

  return {
    estado,
    altitudTexto: elevacion ? `${numeroCO.format(elevacion.altitud_msnm)} msnm` : null,
    // Sin ubicación no se afirma un municipio: solo la región del piloto
    municipioTexto: elevacion?.municipio_nombre
      ? `${elevacion.municipio_nombre}, Huila`
      : elevacion
        ? 'Colombia'
        : 'Huila, Colombia',
    solicitarAltitud: leerUbicacion,
  };
}
