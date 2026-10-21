// src/routes/InicioView.tsx
// Pantalla Inicio. Un solo árbol responsivo: en celular una columna (primero la recomendación) y
// desde 1024 px dos columnas (lote a la izquierda; recomendación, logros y gráficas a la derecha).
// En celular los contenedores de columna son "display: contents" y cada tarjeta se ordena con "order".
'use client';

import { ErrorCard } from '../components/feedback/ErrorCard';
import { FranjaSinConexion } from '../components/feedback/FranjaSinConexion';
import { BotonMicrofono } from '../components/inicio/BotonMicrofono';
import { EncabezadoInicio } from '../components/inicio/EncabezadoInicio';
import { EsqueletoInicio } from '../components/inicio/Esqueleto';
import { GraficaAgua } from '../components/inicio/GraficaAgua';
import { GraficaSuelo } from '../components/inicio/GraficaSuelo';
import { NavegacionPrincipal } from '../components/inicio/NavegacionPrincipal';
import { TarjetaLogros } from '../components/inicio/TarjetaLogros';
import { TarjetaLote, TarjetaMarcarLote } from '../components/inicio/TarjetaLote';
import { TarjetaRecomendacion } from '../components/inicio/TarjetaRecomendacion';
import { clasificarResumen, useResumenInicio } from '../hooks/useResumenInicio';
import type { ResumenInicio } from '../api/tipos';

export function InicioView() {
  const { estado, datos, error, sinConexion, reintentar } = useResumenInicio();

  return (
    <div className="min-h-dvh bg-crema text-tinta lg:pl-64">
      {sinConexion && <FranjaSinConexion />}

      <div className="mx-auto flex max-w-[1280px] flex-col gap-5 px-4 pt-5 pb-36 lg:px-8 lg:pb-12">
        {estado === 'cargando' && <EsqueletoInicio />}

        {estado === 'error' && error && (
          <ErrorCard mensaje={error.mensaje} codigo={error.codigo} onRetry={reintentar} retryLabel="Intentar de nuevo" />
        )}

        {estado === 'listo' && datos && <Contenido datos={datos} />}
      </div>

      <NavegacionPrincipal />
      <BotonMicrofono />
    </div>
  );
}

function Contenido({ datos }: { datos: ResumenInicio }) {
  const clase = clasificarResumen(datos);
  const lote = datos.lote_principal;
  const loteId = lote?.id ?? null;

  return (
    <>
      <EncabezadoInicio nombre={datos.usuario.nombre} ahora={new Date()} clima={datos.clima_hoy} alertas={datos.alertas_pendientes} />

      <main className="flex flex-col gap-5 lg:grid lg:grid-cols-12 lg:items-start">
        <div className="contents lg:col-span-7 lg:flex lg:flex-col lg:gap-5">
          <div className="order-2 lg:order-none">{lote ? <TarjetaLote lote={lote} /> : <TarjetaMarcarLote />}</div>
        </div>

        <div className="contents lg:col-span-5 lg:flex lg:flex-col lg:gap-5">
          <div className="order-1 lg:order-none">
            <TarjetaRecomendacion
              recomendacion={clase.sinRecomendacion ? null : datos.recomendacion_hoy}
              loteId={loteId}
              puedeRegistrarRiego={clase.puedeRegistrarRiego}
            />
          </div>
          <div className="order-3 lg:order-none">
            <TarjetaLogros logros={datos.logros} loteId={loteId} />
          </div>
          {datos.series && (
            <>
              <div className="order-4 lg:order-none">
                <GraficaAgua datos={datos.series.agua_mensual} />
              </div>
              <div className="order-5 lg:order-none">
                <GraficaSuelo datos={datos.series.salud_suelo} />
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
}
