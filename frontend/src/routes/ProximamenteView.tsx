// src/routes/ProximamenteView.tsx
// Secciones de la navegación que todavía no existen: así la navegación y el micrófono no llevan a un 404.
import Link from 'next/link';
import { NavegacionPrincipal } from '../components/inicio/NavegacionPrincipal';

export function ProximamenteView({ titulo, texto }: { titulo: string; texto: string }) {
  return (
    <div className="min-h-dvh bg-crema text-tinta lg:pl-64">
      <main className="mx-auto flex max-w-xl flex-col gap-4 px-4 pt-10 pb-36">
        <h1 className="font-titulo text-3xl font-black text-campo">{titulo}</h1>
        <p className="text-lg text-tinta/80">{texto}</p>
        <p className="text-base text-tinta/70">Estamos trabajando en esta sección.</p>
        <Link href="/inicio" className="text-base font-bold text-campo underline">
          Volver al inicio
        </Link>
      </main>
      <NavegacionPrincipal />
    </div>
  );
}
