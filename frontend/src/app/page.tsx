import { redirect } from "next/navigation";

// Mientras no exista la página de inicio, entramos directo al registro.
export default function Home() {
  redirect("/registro");
}
