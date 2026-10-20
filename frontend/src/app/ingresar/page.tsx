"use client";

import { useRouter } from "next/navigation";
import { IngresarView } from "@/routes/IngresarView";

export default function IngresarPage() {
  const router = useRouter();
  return <IngresarView onNavigate={(path) => router.push(path)} />;
}
