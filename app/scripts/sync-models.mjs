import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const modelRoot = new URL('../../ai/models/', import.meta.url);
const read = async (path) => JSON.parse(await readFile(new URL(path, modelRoot), 'utf8'));
const [context, metrics, training] = await Promise.all([read('context/benelux.json'), read('artifacts/metrics.json'), read('artifacts/training_summary.json')]);
const hash = createHash('sha256');
for (const head of Object.keys(metrics.heads)) {
  for (const quantile of ['p10', 'p50', 'p90']) hash.update(await readFile(new URL(`artifacts/boosters/${head}_${quantile}.txt`, modelRoot)));
}
hash.update(JSON.stringify(context));
const catalog = {
  artifactId: hash.digest('hex').slice(0, 12),
  labelKind: 'synthetic_scenario',
  bbox: context.bbox,
  countries: context.countries,
  projectTypes: context.projectTypes.map(({ id, label, rings }) => ({ id, label, radiusM: rings.at(-1).radiusM, cooling: ['datacentre', 'industrial'].includes(id) })),
  limits: { minYear: 2026, maxYear: 2040, minScale: 0.4, maxScale: 2, maxNearby: 3 },
  metrics,
  training: { n: training.n, split: training.split, sources: training.sources, constantFeatures: training.constantFeatures, missingSources: training.missingSources },
};
const target = new URL('../src/data/impact-catalog.json', import.meta.url);
await writeFile(target, `${JSON.stringify(catalog, null, 2)}\n`);
console.log(`Synced ${catalog.projectTypes.length} project types and model evaluation metadata → ${fileURLToPath(target)}`);
