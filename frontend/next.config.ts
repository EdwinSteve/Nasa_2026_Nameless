import type { NextConfig } from "next";

// En desarrollo la UI llama a /api/v1 en su mismo origen y Next.js lo reenvía a FastAPI:
// así no hace falta CORS. Para apuntar a otro backend, define BACKEND_URL
// (o NEXT_PUBLIC_API_URL para que el navegador lo llame directo).
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/v1/:ruta*", destination: `${BACKEND_URL}/api/v1/:ruta*` }];
  },
};

export default nextConfig;
