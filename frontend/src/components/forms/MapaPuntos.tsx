// src/components/forms/MapaPuntos.tsx
// Mapa satelital donde el productor marca las esquinas de su lote tocando el mapa.
// Solo corre en el navegador: MapDrawer lo carga con next/dynamic y ssr: false.
'use client';

import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect, useMemo, useRef, useState } from 'react';
import { CircleMarker, MapContainer, Marker, Polygon, Polyline, TileLayer, Tooltip, useMap, useMapEvents } from 'react-leaflet';
import type { Coordenada } from '../../api/tipos';

export type Esquina = [number, number]; // [lat, lon], el orden de Leaflet

export interface MapaPuntosProps {
  esquinas: Esquina[];
  cerrado: boolean;
  centroide: Coordenada | null;
  /** A dónde llevar el mapa mientras no haya esquinas (p. ej. el corregimiento de la finca). */
  centro: Coordenada | null;
  interactivo: boolean;
  onAgregar: (esquina: Esquina) => void;
  onMover: (indice: number, esquina: Esquina) => void;
}

// Centro del Huila: vista inicial si todavía no sabemos dónde está la finca
const HUILA: Esquina = [2.535, -75.527];
const ZOOM_HUILA = 9;
const ZOOM_FINCA = 16;
const ZOOM_UBICACION = 17;

const IMAGEN_SATELITAL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
const NOMBRES_LUGARES =
  'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}';
const ATRIBUCION = 'Imágenes © Esri, Maxar, Earthstar Geographics';

// Esquina numerada de 40 px (área táctil) con un círculo visible de 28 px
function iconoEsquina(numero: number, cerrado: boolean): L.DivIcon {
  const fondo = cerrado ? 'bg-[#1F4D2B]' : 'bg-[#E8833A]';
  return L.divIcon({
    className: '',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    html: `<span class="flex h-10 w-10 items-center justify-center"><span class="flex h-7 w-7 items-center justify-center rounded-full border-2 border-white ${fondo} text-sm font-black text-white shadow-md">${numero}</span></span>`,
  });
}

function AlTocar({ activo, onAgregar }: { activo: boolean; onAgregar: (e: Esquina) => void }) {
  useMapEvents({
    click(evento) {
      if (activo) onAgregar([evento.latlng.lat, evento.latlng.lng]);
    },
  });
  return null;
}

/** Lleva el mapa al centro indicado mientras el productor no haya marcado esquinas. */
function Recentrar({ centro, hayEsquinas }: { centro: Coordenada | null; hayEsquinas: boolean }) {
  const mapa = useMap();
  const lat = centro?.lat;
  const lon = centro?.lon;
  // Depende de los números, no del objeto: un objeto nuevo con el mismo centro no mueve el mapa
  useEffect(() => {
    if (lat !== undefined && lon !== undefined && !hayEsquinas) mapa.setView([lat, lon], ZOOM_FINCA);
  }, [lat, lon, hayEsquinas, mapa]);
  return null;
}

/** Al abrir el mapa con un lote ya dibujado, lo encuadra completo. */
function EncuadrarLote({ esquinas }: { esquinas: Esquina[] }) {
  const mapa = useMap();
  const [hecho, setHecho] = useState(false);
  useEffect(() => {
    if (!hecho && esquinas.length >= 3) {
      mapa.fitBounds(L.latLngBounds(esquinas), { padding: [40, 40], maxZoom: 18 });
      setHecho(true);
    }
  }, [esquinas, hecho, mapa]);
  return null;
}

function BotonMiUbicacion() {
  const mapa = useMap();
  const [estado, setEstado] = useState<'listo' | 'buscando' | 'error'>('listo');
  const control = useRef<HTMLDivElement>(null);

  // Leaflet escucha los clics en el contenedor antes que React: sin esto, tocar el botón
  // también marcaría una esquina debajo de él.
  useEffect(() => {
    if (control.current) {
      L.DomEvent.disableClickPropagation(control.current);
      L.DomEvent.disableScrollPropagation(control.current);
    }
  }, []);

  const ubicar = () => {
    if (!('geolocation' in navigator)) {
      setEstado('error');
      return;
    }
    setEstado('buscando');
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        mapa.flyTo([coords.latitude, coords.longitude], ZOOM_UBICACION);
        setEstado('listo');
      },
      () => setEstado('error'),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
    );
  };

  return (
    <div className="leaflet-top leaflet-right">
      <div ref={control} className="leaflet-control">
        <button
          type="button"
          onClick={ubicar}
          className="min-h-11 rounded-xl border-2 border-white bg-white/95 px-3 text-sm font-extrabold text-[#1F4D2B] shadow-md"
        >
          {estado === 'buscando' ? 'Buscando…' : estado === 'error' ? 'Sin ubicación' : 'Mi ubicación'}
        </button>
      </div>
    </div>
  );
}

export default function MapaPuntos({
  esquinas,
  cerrado,
  centroide,
  centro,
  interactivo,
  onAgregar,
  onMover,
}: MapaPuntosProps) {
  const iconos = useMemo(() => esquinas.map((_, i) => iconoEsquina(i + 1, cerrado)), [esquinas, cerrado]);
  const inicio: Esquina = esquinas[0] ?? (centro ? [centro.lat, centro.lon] : HUILA);
  const zoomInicio = esquinas.length || centro ? ZOOM_FINCA : ZOOM_HUILA;

  return (
    <MapContainer
      center={inicio}
      zoom={zoomInicio}
      maxZoom={19}
      className="h-full w-full"
      attributionControl
      scrollWheelZoom
    >
      <TileLayer url={IMAGEN_SATELITAL} attribution={ATRIBUCION} maxNativeZoom={18} maxZoom={19} />
      <TileLayer url={NOMBRES_LUGARES} maxNativeZoom={18} maxZoom={19} />

      <AlTocar activo={interactivo && !cerrado} onAgregar={onAgregar} />
      <Recentrar centro={centro} hayEsquinas={esquinas.length > 0} />
      <EncuadrarLote esquinas={esquinas} />
      <BotonMiUbicacion />

      {cerrado && esquinas.length >= 3 ? (
        <Polygon positions={esquinas} pathOptions={{ color: '#FFFFFF', weight: 3, fillColor: '#6DBE7A', fillOpacity: 0.35 }} />
      ) : (
        esquinas.length >= 2 && (
          <Polyline positions={esquinas} pathOptions={{ color: '#E8833A', weight: 3, dashArray: '6 6' }} />
        )
      )}

      {esquinas.map((esquina, i) => (
        <Marker
          key={i}
          position={esquina}
          icon={iconos[i]}
          draggable={interactivo}
          keyboard={false}
          eventHandlers={{
            dragend: (evento) => {
              const { lat, lng } = (evento.target as L.Marker).getLatLng();
              onMover(i, [lat, lng]);
            },
          }}
        />
      ))}

      {cerrado && centroide && (
        <CircleMarker
          center={[centroide.lat, centroide.lon]}
          radius={8}
          pathOptions={{ color: '#FFFFFF', weight: 3, fillColor: '#4A90C8', fillOpacity: 1 }}
        >
          <Tooltip direction="top" offset={[0, -8]} permanent>
            Punto medio
          </Tooltip>
        </CircleMarker>
      )}
    </MapContainer>
  );
}
