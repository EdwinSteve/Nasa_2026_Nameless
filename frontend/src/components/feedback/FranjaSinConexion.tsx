// Franja fija arriba de la pantalla cuando el navegador se queda sin red.
export function FranjaSinConexion({ texto = 'Sin conexión. Revise sus datos móviles o el wifi.' }: { texto?: string }) {
  return (
    <p role="status" className="sticky top-0 z-[1300] bg-tinta px-4 py-2 text-center text-base font-semibold text-white">
      {texto}
    </p>
  );
}
