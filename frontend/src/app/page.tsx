"use client";

import { useRouter } from "next/navigation";
import { Bienvenida } from "@/routes/Bienvenida";

// Primera vista de SURCO: desde aquí se crea la cuenta o se ingresa.
export default function Home() {
  const router = useRouter();
  return <Bienvenida onCrearCuenta={() => router.push("/registro")} onIngresar={() => router.push("/ingresar")} />;
}
