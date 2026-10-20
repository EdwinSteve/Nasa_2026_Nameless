"use client";

import { useRouter } from "next/navigation";
import { RegistroWizard } from "@/routes/RegistroWizard";

export default function RegistroPage() {
  const router = useRouter();
  return <RegistroWizard onNavigate={(path) => router.push(path)} />;
}
