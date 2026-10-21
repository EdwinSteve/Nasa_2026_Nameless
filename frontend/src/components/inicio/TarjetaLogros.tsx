// "Lo que hemos logrado juntos", o, para un usuario nuevo, lo que va a poder ver aquí.
import Link from 'next/link';
import { useId, type ReactNode } from 'react';
import type { ResumenInicio } from '../../api/tipos';
import { formatearEntero } from '../../lib/fechas';
import { IconoBrote, IconoCalendario, IconoGota, IconoHoja } from '../iconos/Iconos';

const LITROS_POR_TANQUE = 20_000;

function Logro({ icono, cifra, texto, detalle }: { icono: ReactNode; cifra: string; texto: string; detalle: string }) {
  return (
    <li className="flex flex-col gap-1 rounded-2xl bg-crema p-4">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-campo">{icono}</span>
      <span className="mt-1 font-titulo text-2xl font-black text-tinta">{cifra}</span>
      <span className="text-base font-bold text-campo">{texto}</span>
      <span className="text-sm text-tinta/75">{detalle}</span>
    </li>
  );
}

interface Props {
  logros: ResumenInicio['logros'];
  loteId: string | null;
}

export function TarjetaLogros({ logros, loteId }: Props) {
  const idTitulo = useId();

  if (!logros) {
    return (
      <section aria-labelledby={idTitulo} className="flex flex-col gap-3 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
        <h2 id={idTitulo} className="font-titulo text-xl font-extrabold text-tinta">
          Aquí verá cuánta agua ahorra y cómo mejora su suelo
        </h2>
        <p className="text-base text-tinta/80">
          Cuando siembre y riegue con nuestras recomendaciones, iremos sumando lo que logra ciclo a ciclo.
        </p>
        <Link
          href={loteId ? `/lotes/${encodeURIComponent(loteId)}` : '/mis-lotes'}
          className="flex min-h-14 items-center justify-center rounded-full bg-campo px-6 text-base font-bold text-white hover:bg-[#16381F]"
        >
          Ver qué me conviene sembrar
        </Link>
      </section>
    );
  }

  const tanques = Math.round((logros.agua_ahorrada_m3 * 1000) / LITROS_POR_TANQUE);
  const cambio = logros.salud_suelo_cambio;
  return (
    <section aria-labelledby={idTitulo} className="flex flex-col gap-4 rounded-3xl bg-white p-5 shadow-sm lg:p-6">
      <h2 id={idTitulo} className="font-titulo text-xl font-extrabold text-tinta">
        Lo que hemos logrado juntos
      </h2>
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Logro
          icono={<IconoGota tamano={22} />}
          cifra={`${formatearEntero(logros.agua_ahorrada_m3)} m³`}
          texto="de agua ahorrada"
          detalle={`Como ${formatearEntero(tanques)} tanques de ${formatearEntero(LITROS_POR_TANQUE)} litros.`}
        />
        <Logro
          icono={<IconoBrote tamano={22} />}
          cifra={`${formatearEntero(logros.nitrogeno_kg)} kg`}
          texto="de nitrógeno para su suelo"
          detalle="El abono natural que dejó su rotación."
        />
        <Logro
          icono={<IconoHoja tamano={22} />}
          cifra={`${formatearEntero(logros.salud_suelo)} de 100`}
          texto="salud de su suelo"
          detalle={cambio === 0 ? 'Se mantiene estable.' : `${cambio > 0 ? 'Subió' : 'Bajó'} ${formatearEntero(Math.abs(cambio))} puntos.`}
        />
        <Logro
          icono={<IconoCalendario tamano={22} />}
          cifra={`${formatearEntero(logros.frecuencia_exito)} de cada 10 años`}
          texto="sale bien la cosecha"
          detalle="Con su plan actual, según el clima de su zona."
        />
      </ul>
    </section>
  );
}
