import test from 'node:test';
import assert from 'node:assert/strict';
import { projectFields, exampleMeasurements, validateMeasurements, mapMeasurements } from '../src/js/project-inputs.js';
import { compareTreatments, readScenarios, saveScenario, prepareAssessment } from '../src/js/model.js';

const input = () => ({ name: 'Physical inputs', typeId: 'datacentre', center: [4.72,51.797], horizonYear: 2035, scale: 1, inputMode: 'measurements', measurements: exampleMeasurements('datacentre'), cooling: false, buffer: false, nearbyTreatments: [] });
const predict = async (request) => ({ ...request, mitigations: { cooling: request.cooling, buffer: request.buffer }, labelKind: 'synthetic_scenario', sites: [], shapTop: [], dataFlags: {}, outcomes: Object.fromEntries(['habitatHa','riverTempC','vegStress','energyIdx','jobsFte','tco2e'].map((key) => [key,{p10:1,p50:2,p90:3}])) });
const storage = () => { const values = new Map(); return { getItem: (key) => values.get(key) || null, setItem: (key,value) => values.set(key,value) }; };

test('project types show relevant physical quantities, including flow for dams', () => {
  assert.equal(Object.keys(projectFields).length,8);
  assert.deepEqual(projectFields.datacentre.map(({key}) => key),['powerMw','landHa','waterM3Day']);
  assert.deepEqual(projectFields.housing.map(({key}) => key),['homes','landHa','waterM3Day']);
  assert.ok(projectFields.dam.some(({key}) => key === 'flowM3s'));
  assert.ok(projectFields.highway.some(({key}) => key === 'lengthKm'));
  assert.ok(!projectFields.wind.some(({key}) => key === 'waterM3Day'));
});
test('illustrative references map each project type to the same demo size setting', () => {
  for (const typeId of Object.keys(projectFields)) {
    for (const multiplier of [0.5,1,1.5]) assert.equal(mapMeasurements(typeId,exampleMeasurements(typeId,multiplier)).scale,multiplier);
  }
});
test('each physical input affects the demo mapping and freshwater can be zero', () => {
  const base = exampleMeasurements('datacentre');
  for (const key of Object.keys(base)) assert.equal(mapMeasurements('datacentre',{...base,[key]:base[key]*2}).scale,4/3);
  assert.equal(mapMeasurements('datacentre',{...base,waterM3Day:0}).scale,2/3);
});
test('range boundaries are disclosed rather than extrapolated beyond trained scale', () => {
  const high = mapMeasurements('datacentre',exampleMeasurements('datacentre',10));
  assert.equal(high.rawScale,10); assert.equal(high.scale,2); assert.equal(high.limited,true);
  const low = mapMeasurements('datacentre',exampleMeasurements('datacentre',0.01));
  assert.equal(low.scale,0.4); assert.equal(low.limited,true);
});
test('empty, negative, nonfinite and fractional count measurements are rejected', () => {
  for (const patch of [{powerMw:0},{waterM3Day:-1},{waterM3Day:NaN},{landHa:Infinity},{landHa:null},{powerMw:'80'}]) assert.throws(() => prepareAssessment({...input(),measurements:{...input().measurements,...patch}}));
  assert.throws(() => mapMeasurements('housing',{...exampleMeasurements('housing'),homes:2.5}));
  assert.throws(() => prepareAssessment({...input(),measurements:null}));
  assert.deepEqual(validateMeasurements('highway',{}, {required:false}),{lengthKm:null,landHa:null});
});
test('water unit choices convert litres per day to the same canonical volume', () => {
  const units = projectFields.datacentre.find(({key}) => key === 'waterM3Day').units;
  assert.equal(1200000 * units.find(({label}) => label === 'L/day').factor,1200);
  assert.equal(1200 * units.find(({label}) => label === 'm³/day').factor,1200);
});
test('both actual model calls use the same mapped scale and receive only supported fields', async () => {
  const calls = [];
  const run = await compareTreatments({...input(),measurements:{...input().measurements,waterM3Day:2400},cooling:true}, {predict:async (request) => { calls.push(request);return predict(request); }});
  assert.equal(calls.length,2);
  for (const call of calls) {
    assert.equal(call.scale,4/3);
    assert.equal(call.measurements,undefined);
    assert.equal(call.inputMode,undefined);
  }
  assert.equal(run.inputs.measurements.waterM3Day,2400);
  assert.equal(run.mapping.version,'demo-mean-v1');
  assert.equal(run.mapping.references.waterM3Day,1200);
});
test('saved assessments retain physical values and the exact mapping used', async () => {
  const local = storage();
  const run = await compareTreatments(input(),{predict});
  saveScenario(run,local);
  run.inputs.measurements.waterM3Day = 0;
  assert.equal(readScenarios(local)[0].inputs.measurements.waterM3Day,1200);
  assert.equal(readScenarios(local)[0].mapping.references.waterM3Day,1200);
});
test('manual and legacy assessments preserve their original scale and allow empty details', async () => {
  const manual = await compareTreatments({...input(),inputMode:'scale',scale:1.7,measurements:{}},{predict});
  assert.equal(manual.inputs.scale,1.7);assert.equal(manual.mapping,null);
  const legacy = input();delete legacy.inputMode;delete legacy.measurements;
  const {treatment} = prepareAssessment(legacy);
  assert.equal(treatment.scale,1);
});
