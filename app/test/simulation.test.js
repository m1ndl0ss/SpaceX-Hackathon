import test from 'node:test';
import assert from 'node:assert/strict';
import { catalog, projectTypes, validateTreatment, validateReport, compareTreatments, requestPrediction, readScenarios, saveScenario, mitigationComparison, reportWarnings } from '../src/js/model.js';

const input = () => ({ name: 'Test project', typeId: 'datacentre', center: [4.72,51.797], horizonYear: 2035, scale: 1, cooling: false, buffer: false, nearbyTreatments: [] });
const response = (request) => ({
  typeId: request.typeId, center: [...request.center], horizonYear: request.horizonYear,
  mitigations: { cooling: request.cooling, buffer: request.buffer },
  labelKind: 'synthetic_scenario', sites: [], shapTop: [], dataFlags: { gbif: true, water: true },
  outcomes: Object.fromEntries(['habitatHa','riverTempC','vegStress','energyIdx','jobsFte','tco2e'].map((key) => [key, {p10:1,p50:2,p90:3}])),
});
const storage = () => { const map = new Map(); return { getItem:(key) => map.get(key) || null, setItem:(key,value) => map.set(key,value) }; };

test('the catalog exposes all eight team project types and their real model limits', () => {
  assert.deepEqual(projectTypes.map(({id}) => id), ['wind','solar','industrial','highway','housing','dam','powerline','datacentre']);
  assert.equal(catalog.limits.minScale,0.4);
  assert.equal(catalog.limits.maxYear,2040);
  assert.ok(projectTypes.every((type) => type.radiusM > 0));
});
test('the raw model contract contains supported fields only', () => {
  const treatment = validateTreatment({...input(),power:80,water:1200,land:24});
  assert.deepEqual(Object.keys(treatment).sort(), ['typeId','center','horizonYear','scale','cooling','buffer','nearbyTreatments'].sort());
  for (const fields of [{center:[0,0]},{center:[NaN,51]},{center:[4,Infinity]},{scale:NaN},{scale:0},{scale:2.1},{horizonYear:2041},{horizonYear:2030.5},{typeId:'airport'},{typeId:'wind',cooling:true}]) {
    assert.throws(() => validateTreatment({...input(),...fields}));
  }
});
test('nearby projects must have valid types and coordinates and stay within training counts', () => {
  assert.throws(() => validateTreatment({...input(),nearbyTreatments:[{typeId:'highway',center:[0,0]}]}));
  assert.throws(() => validateTreatment({...input(),nearbyTreatments:Array(4).fill({typeId:'housing',center:[4.72,51.797]})}));
  assert.equal(validateTreatment({...input(),nearbyTreatments:[{typeId:'housing',center:[4.72,51.797]}]}).nearbyTreatments.length,1);
});
test('mitigation comparison runs the actual model twice at identical site, year and scale', async () => {
  const calls = [];
  const run = await compareTreatments({...input(),cooling:true,buffer:true}, {predict:async (request) => {calls.push(structuredClone(request));return response(request);}});
  assert.equal(calls.length,2);
  assert.equal(calls[0].cooling,false);
  assert.equal(calls[0].buffer,false);
  assert.equal(calls[1].cooling,true);
  assert.equal(calls[1].buffer,true);
  assert.deepEqual(calls[0].center,calls[1].center);
  assert.equal(calls[0].scale,calls[1].scale);
  assert.equal(calls[0].horizonYear,calls[1].horizonYear);
  assert.ok(run.mitigated);
});
test('no mitigation makes one prediction and does not invent a second result', async () => {
  let count = 0;
  const run = await compareTreatments(input(), {predict:async (request) => {count++;return response(request);}});
  assert.equal(count,1);
  assert.equal(run.mitigated,null);
  assert.equal(mitigationComparison(run),null);
});
test('mismatched, incomplete, nonfinite, or reversed API results are rejected', () => {
  const request = input();
  for (const patch of [{typeId:'wind'},{center:[5,51]},{horizonYear:2040},{mitigations:{cooling:true,buffer:false}},{labelKind:'measured'},{sites:null},{sites:[null]},{sites:[{name:'River',kind:'water',species:'fish'}]},{shapTop:[{feature:null,value:1}]},{shapTarget:'jobsFte'},{dataFlags:{water:'unknown'}}]) assert.throws(() => validateReport({...response(request),...patch},request));
  for (const quantile of [{p10:3,p50:2,p90:1},{p10:0,p50:NaN,p90:1},{p10:-1,p50:0,p90:1},{p10:1,p50:2}]) {
    const report = response(request); report.outcomes.habitatHa = quantile;
    assert.throws(() => validateReport(report,request));
  }
});
test('carbon savings retain negative values and ranges', () => {
  const report = response(input()); report.outcomes.tco2e = {p10:-900,p50:-800,p90:-700};
  assert.equal(validateReport(report,input()).outcomes.tco2e.p50,-800);
});
test('network and service failures never fall back to the previous hand-written formulas', async () => {
  await assert.rejects(requestPrediction(input(),{fetcher:async()=>{throw new Error('Offline');}}),/unavailable/);
  await assert.rejects(requestPrediction(input(),{fetcher:async()=>({ok:false,status:503})}),/could not complete/);
  await assert.rejects(requestPrediction(input(),{fetcher:async()=>({ok:false,status:422})}),/rejected/);
  await assert.rejects(requestPrediction(input(),{fetcher:async()=>({ok:true,json:async()=>{throw new Error('HTML');}})}),/unreadable/);
});
test('the client sends the actual JSON contract to the proxied model endpoint', async () => {
  await requestPrediction(input(),{fetcher:async(url,options)=>{
    assert.equal(url,'/api/impact/infer'); assert.equal(options.method,'POST');
    assert.deepEqual(JSON.parse(options.body),input());
    return {ok:true,json:async()=>response(input())};
  }});
});
test('saved assessments restore their exact input and prediction snapshots', async () => {
  const local = storage();
  const run = await compareTreatments({...input(),buffer:true},{predict:async(request)=>response(request)});
  saveScenario({...run,view:'proposed'},local); run.inputs.center[0] = 6;
  const restored = readScenarios(local)[0];
  assert.equal(restored.inputs.center[0],4.72);
  assert.ok(restored.mitigated);
  assert.equal(restored.view,'proposed');
  saveScenario(restored,local);
  assert.equal(readScenarios(local).length,1);
  assert.throws(() => saveScenario(restored,{getItem:local.getItem,setItem(){throw new Error('Full');}}),/Full/);
});
test('calibration warnings use the team’s stored per-project evidence', () => {
  const warnings = reportWarnings(response(input()));
  assert.ok(warnings.some((warning) => warning.includes('65%')));
  const report = response(input());report.dataFlags.gbif = false;
  assert.ok(reportWarnings(report).some((warning) => warning.includes('species observations')));
});
test('zero baseline habitat estimates do not produce infinite mitigation percentages', () => {
  const base = response(input()); const mitigated = response(input());
  base.outcomes.habitatHa.p50 = 0;
  assert.equal(mitigationComparison({proposed:base,mitigated}).percent,null);
});
test('unexpected mitigation increases are disclosed for each ecological outcome', () => {
  const proposed = response(input()); const mitigated = response(input());
  mitigated.outcomes.riverTempC.p50 = 2.5;
  mitigated.outcomes.vegStress.p50 = 2.5;
  const warnings = reportWarnings(mitigated, {proposed,mitigated});
  assert.ok(warnings.some((warning) => warning.includes('higher river warming, vegetation stress with mitigation')));
});
