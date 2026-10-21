import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  test: {
    include: ["src/**/*.test.ts"],
    // Los formatos es-CO dependen de la zona horaria: se fija la de Colombia
    env: { TZ: "America/Bogota" },
  },
});
