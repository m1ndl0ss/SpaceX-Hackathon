// Versioned frontend presets. These are product-demo values, not trained-model outputs.
export const DEMO_VERSION = 'frontend-demo-v1';
export const demoBaselines = {
  wind:       { habitatHa: 2.8, riverTempC: 0.02, vegStress: 3.2, energyIdx: 0.18, jobsFte: 42, tco2e: -18400 },
  solar:      { habitatHa: 8.4, riverTempC: 0.04, vegStress: 5.6, energyIdx: 0.12, jobsFte: 28, tco2e: -12600 },
  industrial: { habitatHa: 12.6, riverTempC: 0.85, vegStress: 18.4, energyIdx: 1.35, jobsFte: 340, tco2e: 24600 },
  highway:    { habitatHa: 22.4, riverTempC: 0.08, vegStress: 21.6, energyIdx: 0.48, jobsFte: 180, tco2e: 15800 },
  housing:    { habitatHa: 6.8, riverTempC: 0.12, vegStress: 7.8, energyIdx: 0.62, jobsFte: 125, tco2e: 4200 },
  dam:        { habitatHa: 38.2, riverTempC: 1.25, vegStress: 16.2, energyIdx: 0.24, jobsFte: 95, tco2e: -6400 },
  powerline:  { habitatHa: 9.6, riverTempC: 0.01, vegStress: 9.4, energyIdx: 0.32, jobsFte: 64, tco2e: 1800 },
  datacentre: { habitatHa: 10.8, riverTempC: 0.68, vegStress: 12.6, energyIdx: 1.82, jobsFte: 160, tco2e: 19200 },
};

const ecologicalOutcomes = new Set(['habitatHa', 'riverTempC', 'vegStress']);
const bufferFactors = { habitatHa: 0.65, riverTempC: 0.95, vegStress: 0.75, energyIdx: 1, jobsFte: 1.02, tco2e: 0.98 };
const coolingFactors = { habitatHa: 0.96, riverTempC: 0.35, vegStress: 0.85, energyIdx: 1.06, jobsFte: 1.01, tco2e: 1.04 };
const round = (value) => Number(value.toFixed(4));

function distanceM(a, b) {
  const radians = Math.PI / 180;
  const latitude = (b[1] - a[1]) * radians;
  const longitude = (b[0] - a[0]) * radians;
  const h = Math.sin(latitude / 2) ** 2 + Math.cos(a[1] * radians) * Math.cos(b[1] * radians) * Math.sin(longitude / 2) ** 2;
  return 6371000 * 2 * Math.asin(Math.sqrt(Math.min(1, h)));
}

// The caller validates against the same input contract as the optional model API.
export function demoPrediction(treatment) {
  const base = demoBaselines[treatment.typeId];
  if (!base) throw new Error('Select a supported project type.');
  const nearbyFactor = 1 + treatment.nearbyTreatments.reduce((sum, nearby) => {
    const distance = distanceM(treatment.center, nearby.center);
    return sum + (distance <= 500 ? 0.08 : distance <= 2000 ? 0.04 : 0);
  }, 0);
  const yearFactor = 1 + (treatment.horizonYear - 2035) * 0.015;
  const outcomes = Object.fromEntries(Object.entries(base).map(([key, value]) => {
    let estimate = value * treatment.scale * (ecologicalOutcomes.has(key) ? nearbyFactor : yearFactor);
    if (treatment.buffer) estimate *= bufferFactors[key];
    if (treatment.cooling) estimate *= coolingFactors[key];
    const spread = Math.abs(estimate) * 0.2;
    return [key, { p10: round(estimate - spread), p50: round(estimate), p90: round(estimate + spread) }];
  }));
  return {
    typeId: treatment.typeId,
    center: [...treatment.center],
    horizonYear: treatment.horizonYear,
    mitigations: { cooling: treatment.cooling, buffer: treatment.buffer },
    labelKind: 'frontend_demo',
    demoVersion: DEMO_VERSION,
    outcomes,
    sites: [],
    shapTop: [],
    dataFlags: {},
  };
}
