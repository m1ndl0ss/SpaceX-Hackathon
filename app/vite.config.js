import { defineConfig } from "vite";
import { impactServicePlugin, modelTarget } from "./scripts/model-service.mjs";

const proxy = { "/api/impact": { target: modelTarget, changeOrigin: true, rewrite: (path) => path.replace(/^\/api\/impact/, "") } };

export default defineConfig({
  plugins: [impactServicePlugin()],
  server: {
    port: 5173,
    open: true,
    proxy,
  },
  preview: {
    port: 4173,
    proxy,
  },
  optimizeDeps: {
    include: ["mapbox-gl"],
  },
});
