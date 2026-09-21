import catalog from '../data/impact-catalog.json' with { type: 'json' };
import { exampleMeasurements, mapMeasurements, validateMeasurements } from './project-inputs.js';
import { demoPrediction } from './demo-impact.js';
export { catalog };
export const predictionMode = import.meta.env?.VITE_IMPACT_MODE === 'api' ? 'api' : 'demo';
export const isDemoReport = (report) => report?.labelKind === 'frontend_demo';
export const projectTypes = catalog.projectTypes;
export const projectType = (id) => projectTypes.find((item) => item.id === id);
export const outcomeDefinitions = [
  { key: 'habitatHa', label: 'Habitat loss', unit: 'ha', icon: 'bird', digits: 1 },
  { key: 'riverTempC', label: 'River warming', unit: '°C', icon: 'waves', digits: 2 },
  { key: 'vegStress', label: 'Vegetation stress', unit: 'pts', icon: 'leaf', digits: 1 },
  { key: 'energyIdx', label: 'Energy pressure', unit: 'index', icon: 'zap', digits: 2 },
  { key: 'jobsFte', label: 'Employment', unit: 'FTE', icon: 'users', digits: 1 },
  { key: 'tco2e', label: 'Carbon estimate', unit: 'tCO₂e', icon: 'trees', digits: 0 },
];
export const locationPresets = [
  { id: 'dordrecht', name: 'Dordrecht East, Netherlands', center: [4.72, 51.797] },
  { id: 'rotterdam', name: 'Rotterdam, Netherlands', center: [4.48, 51.92] },
  { id: 'limburg', name: 'Maastricht / Limburg', center: [5.696, 50.851] },
  { id: 'namur', name: 'Namur, Belgium', center: [4.87, 50.47] },
  { id: 'luxembourg', name: 'Luxembourg City', center: [6.13, 49.61] },
];
export const simulation = {
  draft: { name: 'Dordrecht East project', typeId: 'datacentre', center: [4.72, 51.797], horizonYear: 2035, inputMode: 'measurements', measurements: exampleMeasurements('datacentre'), scale: 1, cooling: false, buffer: false, nearbyTreatments: [] },
  lastRun: null,
  view: 'proposed',
  dirty: false,
  running: false,
  picking: false,
};
const finite = (number) => typeof number === 'number' && Number.isFinite(number);
export function withinRegion(center) {
  if (!Array.isArray(center) || center.length !== 2 || !center.every(finite)) return false;
  return catalog.countries.some(({ bbox: [west, south, east, north] }) => center[0] >= west && center[0] <= east && center[1] >= south && center[1] <= north);
}
export function validateTreatment(input) {
  if (!projectType(input.typeId)) throw new Error('Select a supported project type.');
  if (!withinRegion(input.center)) throw new Error('Place the project within the supported Benelux region.');
  if (!Number.isInteger(input.horizonYear) || input.horizonYear < catalog.limits.minYear || input.horizonYear > catalog.limits.maxYear) throw new Error('Select a year from 2026 to 2040.');
  if (!finite(input.scale) || input.scale < 0.4 || input.scale > 2) throw new Error('Project scale must be between 0.4× and 2.0×.');
  if (typeof input.cooling !== 'boolean' || typeof input.buffer !== 'boolean') throw new Error('Choose valid mitigation options.');
  if (input.cooling && !projectType(input.typeId).cooling) throw new Error('Closed-loop cooling applies to data centres and industrial plants in this workspace.');
  if (!Array.isArray(input.nearbyTreatments) || input.nearbyTreatments.length > 3) throw new Error('Include up to three nearby projects.');
  for (const nearby of input.nearbyTreatments) {
    if (!projectType(nearby.typeId) || !withinRegion(nearby.center)) throw new Error('Each nearby project needs a supported type and valid Benelux coordinates.');
  }
  const { typeId, center, horizonYear, scale, cooling, buffer, nearbyTreatments } = input;
  return structuredClone({ typeId, center, horizonYear, scale, cooling, buffer, nearbyTreatments });
}
export function prepareAssessment(input) {
  const inputMode = input.inputMode || 'scale';
  if (!['scale', 'measurements'].includes(inputMode)) throw new Error('Select a supported project input mode.');
  const measurements = input.measurements ? validateMeasurements(input.typeId, input.measurements, { required: inputMode === 'measurements' }) : null;
  const mapping = inputMode === 'measurements' ? mapMeasurements(input.typeId, measurements) : null;
  const treatment = validateTreatment({ ...input, scale: mapping?.scale ?? input.scale });
  return { treatment, inputMode, measurements, mapping };
}
export function validateReport(report, request) {
  if (!report || report.typeId !== request.typeId || report.horizonYear !== request.horizonYear || !Array.isArray(report.center) || report.center.length !== 2 || report.center.some((value, index) => !finite(value) || Math.abs(value - request.center[index]) > 1e-6) || report.mitigations?.cooling !== request.cooling || report.mitigations?.buffer !== request.buffer) throw new Error('The model returned a result for different inputs. Run the assessment again.');
  for (const { key } of outcomeDefinitions) {
    const quantile = report.outcomes?.[key];
    if (!quantile || ![quantile.p10, quantile.p50, quantile.p90].every(finite) || quantile.p10 > quantile.p50 || quantile.p50 > quantile.p90 || (key !== 'tco2e' && quantile.p10 < 0)) throw new Error('The model returned incomplete or invalid prediction ranges. No new results have been displayed.');
  }
  if (!['synthetic_scenario', 'frontend_demo'].includes(report.labelKind) || !Array.isArray(report.sites) || !Array.isArray(report.shapTop)) throw new Error('The result does not match the supported impact report format.');
  if (isDemoReport(report) && (typeof report.demoVersion !== 'string' || !report.demoVersion || report.sites.length || report.shapTop.length)) throw new Error('The demo result contains invalid source information.');
  const invalidSites = report.sites.some((site) => !site || typeof site.name !== 'string' || !['habitat', 'water'].includes(site.kind) || (site.distanceM != null && (!finite(site.distanceM) || site.distanceM < 0)) || !Array.isArray(site.species) || site.species.some((species) => typeof species !== 'string'));
  const invalidDrivers = report.shapTop.some((item) => !item || typeof item.feature !== 'string' || !finite(item.value));
  if (invalidSites || invalidDrivers || (report.shapTarget && report.shapTarget !== 'habitatHa') || !report.dataFlags || Array.isArray(report.dataFlags) || typeof report.dataFlags !== 'object' || Object.values(report.dataFlags).some((value) => typeof value !== 'boolean')) throw new Error('The model returned invalid supporting evidence. No new results have been displayed.');
  return report;
}
export async function requestDemoPrediction(treatment, { signal } = {}) {
  signal?.throwIfAborted();
  const input = validateTreatment(treatment);
  return validateReport(demoPrediction(input), input);
}
export async function requestPrediction(treatment, { signal, fetcher = fetch } = {}) {
  let response;
  try {
    response = await fetcher('/api/impact/infer', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(treatment), signal });
  } catch (error) {
    if (error.name === 'AbortError' || signal?.aborted) throw error;
    throw new Error('The impact model service is unavailable. Check that the local model runtime is installed and running, then retry.');
  }
  if (!response.ok) {
    if (response.status === 422) throw new Error('The model rejected these project inputs. Check the location, scale, year, and nearby projects.');
    throw new Error('The impact model service could not complete this assessment. Check its runtime and model artifacts, then retry.');
  }
  let body;
  try { body = await response.json(); } catch { throw new Error('The model service returned an unreadable response. Please retry.'); }
  if (body?.labelKind !== 'synthetic_scenario') throw new Error('The model service returned an unsupported result source.');
  return validateReport(body, treatment);
}
export async function compareTreatments(input, options = {}) {
  const { treatment, inputMode, measurements, mapping } = prepareAssessment(input);
  const proposedInput = { ...treatment, cooling: false, buffer: false };
  const predict = options.predict || (predictionMode === 'api' ? requestPrediction : requestDemoPrediction);
  const [proposed, mitigated] = await Promise.all([
    predict(proposedInput, options),
    treatment.cooling || treatment.buffer ? predict(treatment, options) : Promise.resolve(null),
  ]);
  validateReport(proposed, proposedInput);
  if (mitigated) validateReport(mitigated, treatment);
  if (mitigated && (mitigated.labelKind !== proposed.labelKind || mitigated.demoVersion !== proposed.demoVersion)) throw new Error('Both comparisons must use the same result source.');
  return { id: crypto.randomUUID(), createdAt: new Date().toISOString(), artifactId: isDemoReport(proposed) ? proposed.demoVersion : catalog.artifactId, inputs: { ...treatment, inputMode, measurements, name: String(input.name || projectType(treatment.typeId).label).trim().slice(0, 120) }, mapping, proposed, mitigated };
}
export function selectedReport() {
  return simulation.lastRun?.[simulation.view] || simulation.lastRun?.proposed || null;
}
export function mitigationComparison(run) {
  if (!run?.mitigated) return null;
  const before = run.proposed.outcomes.habitatHa.p50;
  const after = run.mitigated.outcomes.habitatHa.p50;
  return { difference: after - before, percent: before > 0 ? (after - before) / before * 100 : null };
}
export function reportWarnings(report, run = simulation.lastRun) {
  if (isDemoReport(report)) return [];
  const warnings = [];
  for (const outcome of outcomeDefinitions) {
    const stats = catalog.metrics.heads[outcome.key]?.byType?.[report.typeId];
    if (stats && stats.coverage80 < 0.7) warnings.push(`${outcome.label}: the nominal 80% range covered only ${(stats.coverage80 * 100).toFixed(0)}% of synthetic test cases for this project type.`);
  }
  const missing = Object.entries(report.dataFlags || {}).filter(([name, available]) => !available && name !== 'news').map(([name]) => ({gbif:'species observations', roadkill:'roadkill records', protected_areas:'protected areas', water:'water features', osm_roads:'roads', open_meteo:'weather'}[name] || name));
  if (missing.length) warnings.push(`Missing source data: ${missing.join(', ')}. Missing observations do not establish the absence of ecological risk.`);
  if (run?.mitigated === report) {
    const increased = outcomeDefinitions.filter(({ key }) => ['habitatHa', 'riverTempC', 'vegStress'].includes(key) && report.outcomes[key].p50 > run.proposed.outcomes[key].p50 + 1e-6).map(({ label }) => label.toLowerCase());
    if (increased.length) warnings.push(`This run predicts higher ${increased.join(', ')} with mitigation. The trained model does not guarantee the expected mitigation direction.`);
  }
  return warnings;
}

const SAVED_KEY = 'yosemite.impact-assessments.v1';
export function readScenarios(storage = localStorage) {
  const parsed = JSON.parse(storage.getItem(SAVED_KEY) || '[]');
  if (!Array.isArray(parsed)) throw new Error('Saved assessments could not be read.');
  return parsed.filter((run) => {
    try {
      const input = validateTreatment(run.inputs);
      if (run.inputs.inputMode === 'measurements') {
        validateMeasurements(input.typeId, run.inputs.measurements, { required: true });
        if (!run.mapping || typeof run.mapping.version !== 'string' || run.mapping.scale !== input.scale) return false;
      }
      if (!run.id || !Number.isFinite(Date.parse(run.createdAt))) return false;
      validateReport(run.proposed, { ...input, cooling: false, buffer: false });
      if (input.cooling || input.buffer) {
        validateReport(run.mitigated, input);
        if (run.mitigated.labelKind !== run.proposed.labelKind || run.mitigated.demoVersion !== run.proposed.demoVersion) return false;
      }
      return true;
    } catch { return false; }
  });
}
export function saveScenario(run, storage = localStorage) {
  const saved = readScenarios(storage);
  const snapshot = structuredClone(run);
  const next = [snapshot, ...saved.filter((item) => item.id !== snapshot.id)];
  storage.setItem(SAVED_KEY, JSON.stringify(next));
  return next;
}
