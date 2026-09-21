import test from 'node:test';
import assert from 'node:assert/strict';
import { demoBaselines, DEMO_VERSION } from '../src/js/demo-impact.js';
import { projectTypes, compareTreatments, requestDemoPrediction, requestPrediction, validateReport, reportWarnings, readScenarios, saveScenario } from '../src/js/model.js';
import { exampleMeasurements } from '../src/js/project-inputs.js';

const input = (fields = {}) => ({ name: 'Browser project', typeId: 'datacentre', center: [4.72, 51.797], horizonYear: 2035, scale: 1, cooling: false, buffer: false, nearbyTreatments: [], ...fields });

test('every project type works without a model API and has distinct, stable outcomes', async () => {
  const habitats = new Set();
  const fetcher = () => { throw new Error('No server available'); };
  for (const { id } of projectTypes) {
    const run = await compareTreatments(input({ typeId: id }), { fetcher });
    const repeat = await compareTreatments(input({ typeId: id }), { fetcher });
    assert.deepEqual(run.proposed, repeat.proposed);
    assert.equal(run.artifactId, DEMO_VERSION);
    assert.equal(run.proposed.labelKind, 'frontend_demo');
    assert.equal(run.proposed.outcomes.habitatHa.p50, demoBaselines[id].habitatHa);
    assert.equal(Object.keys(run.proposed.outcomes).length, 6);
    assert.deepEqual(run.proposed.sites, []);
    assert.deepEqual(run.proposed.shapTop, []);
    assert.deepEqual(reportWarnings(run.proposed), []);
    habitats.add(run.proposed.outcomes.habitatHa.p50);
    for (const { p10, p50, p90 } of Object.values(run.proposed.outcomes)) {
      assert.ok([p10, p50, p90].every(Number.isFinite));
      assert.ok(p10 <= p50 && p50 <= p90);
    }
  }
  assert.equal(habitats.size, projectTypes.length);
});

test('resource selectors, size and year affect the browser scenario', async () => {
  const baseline = await compareTreatments(input({ inputMode: 'measurements', measurements: exampleMeasurements('datacentre') }));
  const water = await compareTreatments(input({ inputMode: 'measurements', measurements: { ...exampleMeasurements('datacentre'), waterM3Day: 2400 } }));
  assert.ok(water.proposed.outcomes.riverTempC.p50 > baseline.proposed.outcomes.riverTempC.p50);
  assert.ok(water.proposed.outcomes.habitatHa.p50 > baseline.proposed.outcomes.habitatHa.p50);
  const later = await compareTreatments(input({ horizonYear: 2040 }));
  assert.ok(later.proposed.outcomes.jobsFte.p50 > baseline.proposed.outcomes.jobsFte.p50);
  assert.equal(later.proposed.outcomes.habitatHa.p50, baseline.proposed.outcomes.habitatHa.p50);
  const high = await compareTreatments(input({ scale: 2 }));
  assert.equal(high.proposed.outcomes.habitatHa.p50, baseline.proposed.outcomes.habitatHa.p50 * 2);
});

test('mitigation lowers ecological impacts and keeps cooling tradeoffs', async () => {
  for (const { id, cooling } of projectTypes) {
    const run = await compareTreatments(input({ typeId: id, buffer: true, cooling }));
    for (const key of ['habitatHa', 'riverTempC', 'vegStress']) assert.ok(run.mitigated.outcomes[key].p50 < run.proposed.outcomes[key].p50);
    if (cooling) assert.ok(run.mitigated.outcomes.energyIdx.p50 > run.proposed.outcomes.energyIdx.p50);
    if (['wind', 'solar', 'dam'].includes(id)) assert.ok(run.mitigated.outcomes.tco2e.p90 < 0);
  }
});

test('nearby-project adjustments respect distance instead of just counting entries', async () => {
  const baseline = await requestDemoPrediction(input());
  const close = await requestDemoPrediction(input({ nearbyTreatments: [{ typeId: 'housing', center: [4.72, 51.797] }] }));
  const middle = await requestDemoPrediction(input({ nearbyTreatments: [{ typeId: 'housing', center: [4.72, 51.807] }] }));
  const far = await requestDemoPrediction(input({ nearbyTreatments: [{ typeId: 'housing', center: [6.13, 49.61] }] }));
  assert.ok(close.outcomes.habitatHa.p50 > middle.outcomes.habitatHa.p50);
  assert.ok(middle.outcomes.habitatHa.p50 > baseline.outcomes.habitatHa.p50);
  assert.deepEqual(far.outcomes, baseline.outcomes);
});

test('demo assessments preserve exact results and source when saved and restored', async () => {
  const values = new Map();
  const storage = { getItem: (key) => values.get(key) || null, setItem: (key, value) => values.set(key, value) };
  const run = await compareTreatments(input({ cooling: true, buffer: true }));
  saveScenario(run, storage);
  assert.deepEqual(readScenarios(storage), [run]);
  assert.equal(readScenarios(storage)[0].proposed.demoVersion, DEMO_VERSION);
  run.proposed.outcomes.habitatHa.p50 = 0;
  assert.notEqual(readScenarios(storage)[0].proposed.outcomes.habitatHa.p50, 0);
});

test('demo mode validates inputs, supports cancellation and cannot pose as an API result', async () => {
  await assert.rejects(requestDemoPrediction(input({ scale: 0 })), /scale/);
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(requestDemoPrediction(input(), { signal: controller.signal }), { name: 'AbortError' });
  const report = await requestDemoPrediction(input());
  assert.throws(() => validateReport({ ...report, demoVersion: undefined }, input()), /source/);
  assert.throws(() => validateReport({ ...report, shapTop: [{ feature: 'scale', value: 1 }] }, input()), /source/);
  await assert.rejects(requestPrediction(input(), { fetcher: async () => ({ ok: true, json: async () => report }) }), /source/);
});
