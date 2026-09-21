const capacity = { key: 'capacityMw', label: 'Generation capacity', units: [{ label: 'MW', factor: 1 }, { label: 'kW', factor: 0.001 }], positive: true };
const power = { ...capacity, key: 'powerMw', label: 'Electricity demand' };
const land = { key: 'landHa', label: 'Site footprint', units: [{ label: 'ha', factor: 1 }, { label: 'm²', factor: 0.0001 }], positive: true };
const water = { key: 'waterM3Day', label: 'Freshwater withdrawal', units: [{ label: 'm³/day', factor: 1 }, { label: 'L/day', factor: 0.001 }], positive: false, help: 'Average daily intake during operation, before any selected mitigation. Enter 0 for no freshwater withdrawal.' };
const length = { key: 'lengthKm', label: 'Route length', units: [{ label: 'km', factor: 1 }, { label: 'm', factor: 0.001 }], positive: true };

export const projectFields = {
  wind: [capacity, { ...land, label: 'Land occupied by infrastructure' }],
  solar: [capacity, land, water],
  industrial: [power, land, water],
  highway: [length, land],
  housing: [{ key: 'homes', label: 'Number of homes', units: [{ label: 'homes', factor: 1 }], positive: true, integer: true }, land, water],
  dam: [capacity, { ...land, label: 'Reservoir area' }, { key: 'flowM3s', label: 'Water flow through turbines', units: [{ label: 'm³/s', factor: 1 }, { label: 'L/s', factor: 0.001 }], positive: true }],
  powerline: [length, { ...land, label: 'Corridor footprint' }],
  datacentre: [power, land, water],
};

// Illustrative UI reference projects, not engineering standards or model calibration.
export const demoReferences = {
  wind: { capacityMw: 30, landHa: 6 },
  solar: { capacityMw: 50, landHa: 60, waterM3Day: 20 },
  industrial: { powerMw: 20, landHa: 15, waterM3Day: 1000 },
  highway: { lengthKm: 10, landHa: 30 },
  housing: { homes: 200, landHa: 10, waterM3Day: 100 },
  dam: { capacityMw: 20, landHa: 100, flowM3s: 50 },
  powerline: { lengthKm: 20, landHa: 60 },
  datacentre: { powerMw: 80, landHa: 24, waterM3Day: 1200 },
};
export const DEMO_MAPPING_VERSION = 'demo-mean-v1';

export function exampleMeasurements(typeId, multiplier = 1) {
  return Object.fromEntries(projectFields[typeId].map(({ key, integer }) => [key, integer ? Math.max(1, Math.round(demoReferences[typeId][key] * multiplier)) : demoReferences[typeId][key] * multiplier]));
}

export function mapMeasurements(typeId, values) {
  const measurements = validateMeasurements(typeId, values, { required: true });
  const references = { ...demoReferences[typeId] };
  const rawScale = Object.keys(measurements).reduce((sum, key) => sum + measurements[key] / references[key], 0) / Object.keys(measurements).length;
  if (!Number.isFinite(rawScale)) throw new Error('These project measurements are too large to assess.');
  return { version: DEMO_MAPPING_VERSION, scale: Math.min(2, Math.max(0.4, rawScale)), rawScale, limited: rawScale < 0.4 || rawScale > 2, references };
}

export function emptyMeasurements(typeId) {
  return Object.fromEntries(projectFields[typeId].map(({ key }) => [key, null]));
}

export function validateMeasurements(typeId, values, { required = false } = {}) {
  const fields = projectFields[typeId];
  if (!fields || !values || typeof values !== 'object' || Array.isArray(values)) throw new Error('Enter valid project measurements.');
  return Object.fromEntries(fields.map(({ key, label, positive, integer }) => {
    const value = values[key];
    if (value === null || value === undefined) {
      if (required) throw new Error(`Enter ${label.toLowerCase()} to run the assessment.`);
      return [key, null];
    }
    if (typeof value !== 'number' || !Number.isFinite(value) || (positive ? value <= 0 : value < 0) || (integer && !Number.isSafeInteger(value))) throw new Error(`${label} must be ${integer ? 'a whole number greater than zero' : positive ? 'greater than zero' : 'zero or greater'}.`);
    return [key, value];
  }));
}

export function measurementSummary(typeId, values) {
  return projectFields[typeId].filter(({ key }) => Number.isFinite(values?.[key])).map(({ key, label, units }) => ({ label, value: values[key], unit: units[0].label }));
}
