import { redirect } from "next/navigation";

// Ruta anterior del menú: el plan de siembra ahora vive en /plan
export default function Pagina() {
  redirect("/plan");
}
