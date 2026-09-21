import { defineConfig, loadEnv } from "vite";
import { impactServicePlugin, modelTarget } from "./scripts/model-service.mjs";

const proxy = { "/api/impact": { target: modelTarget, changeOrigin: true, rewrite: (path) => path.replace(/^\/api\/impact/, "") } };

export default defineConfig(({ mode }) => {
  const impactMode = loadEnv(mode, process.cwd(), 'VITE_').VITE_IMPACT_MODE || 'demo';
  if (!['demo', 'api'].includes(impactMode)) throw new Error('VITE_IMPACT_MODE must be demo or api.');
  const useApi = impactMode === 'api';
  return {
    plugins: useApi ? [impactServicePlugin()] : [],
    server: {
      port: 5173,
      open: true,
      proxy: useApi ? proxy : undefined,
    },
    preview: {
      port: 4173,
      proxy: useApi ? proxy : undefined,
    },
    optimizeDeps: {
      include: ["mapbox-gl"],
    },
  };
});
