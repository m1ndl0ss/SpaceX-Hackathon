import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export const modelSource = fileURLToPath(new URL('../../ai/models/src', import.meta.url));
export const defaultPython = fileURLToPath(new URL('../.model-venv/bin/python', import.meta.url));
export const modelTarget = process.env.IMPACT_MODEL_URL || 'http://127.0.0.1:8765';

export function launchModelService() {
  const python = process.env.MODEL_PYTHON || defaultPython;
  if (!existsSync(python) && !process.env.MODEL_PYTHON) {
    console.warn('[impact] Run npm run models:setup to install the model runtime. Simulation will report that the service is unavailable until it is installed.');
    return null;
  }
  const child = spawn(python, ['-B', '-m', 'impact_models.serve', '--host', '127.0.0.1', '--port', '8765'], {
    env: { ...process.env, PYTHONPATH: [modelSource, process.env.PYTHONPATH].filter(Boolean).join(':'), PYTHONDONTWRITEBYTECODE: '1', OMP_NUM_THREADS: '1', OPENBLAS_NUM_THREADS: '1' },
    stdio: ['ignore', 'inherit', 'inherit'],
  });
  child.on('error', (error) => console.error(`[impact] Model service could not start: ${error.message}. Run npm run models:setup.`));
  return child;
}

export function impactServicePlugin() {
  const configure = (server) => {
    let child;
    let closed = false;
    const stop = () => { closed = true; if (child && child.exitCode === null) child.kill('SIGTERM'); };
    server.httpServer?.once('close', stop);
    server.httpServer?.once('listening', async () => {
      if (process.env.IMPACT_MODEL_URL) return;
      try {
        const response = await fetch(`${modelTarget}/health`, { signal: AbortSignal.timeout(1500) });
        const health = await response.json();
        if (response.ok && health.ok && health.warehouse) return;
      } catch { /* Start the local service if none is already running. */ }
      if (!closed) child = launchModelService();
    });
  };
  return { name: 'local-impact-model-service', configureServer: configure, configurePreviewServer: configure };
}
