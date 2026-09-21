import '../project-inputs.css';
import '../simulation-layout.css';
import { $, $$ } from './dom.js';
import { renderIcons } from './icons.js';
import { toast } from './toast.js';
import { state } from './state.js';
import { drawAll, focusSimulation, pickSimulationLocation } from './maps.js';
import { escapeHtml as e, formatDate } from './format.js';
import { catalog, simulation, projectTypes, projectType, outcomeDefinitions, locationPresets, compareTreatments, selectedReport, mitigationComparison, reportWarnings, prepareAssessment, readScenarios, saveScenario, predictionMode, isDemoReport } from './model.js';
import { projectFields, demoReferences, exampleMeasurements, emptyMeasurements, mapMeasurements, measurementSummary } from './project-inputs.js';

let requestId = 0;
let controller;
let saved = [];
const measurementDrafts = new Map();
function showPanel(panel) {
  $('#lm-simulation').dataset.panel = panel;
  $$('[data-sim-panel]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.simPanel === panel)));
  requestAnimationFrame(drawAll);
}
const status = (text) => { $('#lm-input-status').textContent = text; };
const showError = (message = '') => {
  $('#lm-simulation-error').textContent = message;
  $('#lm-simulation-error').hidden = !message;
};
const number = (value, digits) => new Intl.NumberFormat(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value);
const typeOptions = (selected) => projectTypes.map((type) => `<option value="${type.id}" ${type.id === selected ? 'selected' : ''}>${e(type.label)}</option>`).join('');

function readInputs() {
  const input = {
    name: $('#lm-project-name').value.trim(),
    typeId: $('#lm-project-type').value,
    center: [$('#lm-longitude').valueAsNumber, $('#lm-latitude').valueAsNumber],
    horizonYear: Number($('#lm-project-year').value),
    scale: Number($('#lm-project-scale').value),
    inputMode: $('#lm-input-mode').value,
    measurements: Object.fromEntries($$('[data-project-measurement]').map((row) => {
      const field = row.querySelector('input');
      return [row.dataset.projectMeasurement, field.value === '' ? null : field.valueAsNumber * Number(row.querySelector('select')?.value || 1)];
    })),
    cooling: $('#lm-cooling').checked,
    buffer: $('#lm-buffer').checked,
    nearbyTreatments: $$('.lm-nearby-row').map((row) => ({ typeId: row.querySelector('select').value, center: [row.querySelector('[data-longitude]').valueAsNumber, row.querySelector('[data-latitude]').valueAsNumber] })),
  };
  if (input.inputMode === 'measurements') {
    try { input.scale = mapMeasurements(input.typeId, input.measurements).scale; } catch { /* Validate incomplete edits when submitted. */ }
  }
  return input;
}
function renderMeasurements() {
  const input = simulation.draft;
  $('#lm-project-measurements').innerHTML = projectFields[input.typeId].map(({ key, label, units, integer, help }) => `<div class="lm-measurement-field" data-project-measurement="${key}"><label for="lm-measure-${key}">${e(label)}</label><div class="lm-measurement-control"><input id="lm-measure-${key}" type="number" min="${integer ? 1 : 0}" step="${integer ? 1 : 'any'}" value="${Number.isFinite(input.measurements?.[key]) ? input.measurements[key] : ''}" placeholder="Enter amount" ${input.inputMode === 'measurements' ? 'required' : ''}>${units.length > 1 ? `<select aria-label="${e(label)} unit" data-measurement-unit>${units.map(({ label, factor }) => `<option value="${factor}">${e(label)}</option>`).join('')}</select>` : `<span class="lm-measurement-unit">${e(units[0].label)}</span>`}</div>${help ? `<p class="lm-field-help">${e(help)}</p>` : ''}</div>`).join('');
  $('#lm-mapping-references').innerHTML = measurementSummary(input.typeId, demoReferences[input.typeId]).map(({ label, value, unit }) => `<div><span>${e(label)}</span><strong>${number(value, 0)} ${e(unit)}</strong></div>`).join('');
}
function updateMapping() {
  const input = simulation.draft;
  $('#lm-input-mode').value = input.inputMode || 'scale';
  $('#lm-manual-scale').hidden = input.inputMode === 'measurements';
  $$('[data-project-measurement] input').forEach((field) => { field.required = input.inputMode === 'measurements'; });
  const limit = $('#lm-measurement-limit');
  limit.hidden = true;
  const example = [0.5, 1, 1.5].find((factor) => Object.entries(exampleMeasurements(input.typeId, factor)).every(([key, value]) => Math.abs((input.measurements?.[key] ?? NaN) - value) < 1e-8));
  $('#lm-project-example').value = example ? String(example) : 'custom';
  if (input.inputMode !== 'measurements') {
    $('#lm-mapping-status').textContent = `Using the manually selected ${number(input.scale, 2)}× model factor. Measurements are saved as project details.`;
    return;
  }
  try {
    const mapping = mapMeasurements(input.typeId, input.measurements);
    $('#lm-mapping-status').textContent = `Demo conversion: ${number(mapping.rawScale, 2)}× → model factor ${number(mapping.scale, 2)}×. These references are uncalibrated demo assumptions.`;
    if (mapping.limited) {
      limit.hidden = false;
      limit.textContent = `These inputs map to ${number(mapping.rawScale, 2)}×, outside the model’s 0.4–2.0× range. Predictions use the ${number(mapping.scale, 2)}× boundary. Changes beyond it may produce identical results; your actual inputs will still be saved.`;
    }
  } catch (error) { $('#lm-mapping-status').textContent = error.message; }
}
function updateInputChrome() {
  const type = projectType(simulation.draft.typeId);
  $('#lm-cooling-field').hidden = !type.cooling;
  $('#lm-scale-value').textContent = `${simulation.draft.scale.toFixed(2)}×`;
  updateMapping();
  $('#lm-project-map-title').textContent = `${type.label} · screening area`;
  $('#lm-map-location').textContent = simulation.draft.center.every(Number.isFinite) ? `${simulation.draft.center[0].toFixed(4)}° E, ${simulation.draft.center[1].toFixed(4)}° N` : 'Enter valid coordinates';
  $('#lm-screening-radius').textContent = `${number(type.radiusM, 0)} m`;
  $('#lm-nearby-count').textContent = `(${simulation.draft.nearbyTreatments.length})`;
  $('#lm-add-nearby').disabled = simulation.draft.nearbyTreatments.length >= catalog.limits.maxNearby;
}
function renderInputs() {
  const input = simulation.draft;
  $('#lm-project-name').value = input.name;
  $('#lm-project-type').value = input.typeId;
  $('#lm-longitude').value = input.center[0];
  $('#lm-latitude').value = input.center[1];
  $('#lm-project-location').value = locationPresets.find((item) => item.center.every((value, index) => value === input.center[index]))?.id || 'custom';
  $('#lm-project-year').value = input.horizonYear;
  $('#lm-project-scale').value = input.scale;
  $('#lm-input-mode').value = input.inputMode || 'scale';
  renderMeasurements();
  $('#lm-cooling').checked = input.cooling;
  $('#lm-buffer').checked = input.buffer;
  $('#lm-nearby-projects').innerHTML = input.nearbyTreatments.map((nearby, index) => `<div class="lm-nearby-row">
    <label>Nearby project ${index + 1}<select aria-label="Nearby project ${index + 1} type">${typeOptions(nearby.typeId)}</select></label>
    <div class="lm-form-grid"><label>Longitude<input type="number" step="any" data-longitude aria-label="Nearby project ${index + 1} longitude" value="${e(nearby.center[0])}" required></label><label>Latitude<input type="number" step="any" data-latitude aria-label="Nearby project ${index + 1} latitude" value="${e(nearby.center[1])}" required></label></div>
    <button type="button" class="lm-button" data-remove-nearby="${index}" aria-label="Remove nearby project ${index + 1}">Remove</button></div>`).join('');
  updateInputChrome();
}
function stopPending() {
  requestId += 1;
  controller?.abort();
  controller = null;
  simulation.running = false;
  $('#lm-run').disabled = false;
  $('#lm-run span').textContent = 'Run assessment';
}
function markDirty() {
  stopPending();
  simulation.dirty = true;
  showError();
  updateInputChrome();
  status(simulation.lastRun ? 'Inputs changed · run again to update the results.' : 'Ready to run your project assessment.');
  renderResults();
}
function refreshSaved() {
  try {
    saved = readScenarios();
    $('#lm-saved-scenarios').innerHTML = '<option value="">Saved assessments</option>' + saved.map((run) => `<option value="${e(run.id)}">${e(run.inputs.name)} · ${e(formatDate(run.createdAt))}</option>`).join('');
  } catch { toast('Saved assessments could not be read from this browser.'); }
}

export function renderResults() {
  const run = simulation.lastRun;
  const report = selectedReport();
  const demo = report ? isDemoReport(report) : predictionMode === 'demo';
  $('#lm-model-scope').hidden = demo;
  $('.lm-simulation-sites').hidden = demo;
  $('#lm-trained-model-details').hidden = demo;
  $('#lm-demo-method').hidden = !demo;
  $('#lm-evidence-title').textContent = demo ? 'Simulation details' : 'Model evidence and limitations';
  $('#lm-habitat-chart').setAttribute('aria-label', demo ? 'Habitat loss comparison and scenario ranges' : 'Model habitat loss estimates and prediction ranges');
  $('#lm-chart-caption').textContent = demo ? 'Dots: estimate · lines: scenario range · lower is better' : 'Dots: p50 estimate · lines: p10–p90 range · lower is better';
  $('#lm-save').disabled = !run || simulation.dirty || simulation.running;
  $('#lm-no-results').hidden = Boolean(run);
  $('#lm-result-content').hidden = !run;
  $('#lm-stale-results').hidden = !run || !simulation.dirty;
  $$('[data-view]').forEach((button) => {
    button.disabled = !run || (button.dataset.view === 'mitigated' && !run.mitigated);
    button.setAttribute('aria-pressed', String(button.dataset.view === simulation.view));
  });
  if (!report) { drawAll(); return; }
  $('#lm-results-title').textContent = `Impact estimates · ${run.inputs.horizonYear}`;
  $('#lm-run-summary').textContent = `${run.inputs.name} · ${projectType(run.inputs.typeId).label} · ${run.inputs.center.map((value) => value.toFixed(4)).join(', ')} · ${simulation.view === 'mitigated' ? 'Selected mitigation' : 'Without mitigation'}`;
  const measurements = measurementSummary(run.inputs.typeId, run.inputs.measurements);
  $('#lm-measurement-summary').innerHTML = measurements.length ? measurements.map(({ label, value, unit }) => `<div><span>${e(label)}</span><strong>${number(value, value % 1 ? 2 : 0)} ${e(unit)}</strong></div>`).join('') : '<p class="lm-field-help">This saved assessment used a model factor without physical measurements.</p>';
  $('#lm-measurement-method').textContent = run.mapping ? `Demo approximation (${run.mapping.version}): entered measurements were combined into a ${number(run.inputs.scale, 2)}× size factor. Water, land, and capacity effects are not modeled independently.${run.mapping.limited ? ` The calculated ${number(run.mapping.rawScale, 2)}× exceeded the supported range, so these results use its boundary.` : ''} These measurements describe the project before mitigation.` : `Manual model factor: ${number(run.inputs.scale, 2)}×. Recorded measurements did not influence these predictions.`;
  $('#lm-impact-results').innerHTML = outcomeDefinitions.map(({ key, label, unit, digits }) => {
    const q = report.outcomes[key];
    return `<div class="lm-result"><div class="lm-result-icon"><span>${e(label)}</span></div><div class="lm-result-val">${number(q.p50, digits)}<small> ${e(unit)}</small></div><div class="lm-result-label">${demo ? 'Scenario estimate' : 'Model p50 estimate'}</div><div class="lm-result-range">${demo ? 'Range' : 'p10–p90'}: ${number(q.p10, digits)} to ${number(q.p90, digits)} ${e(unit)}</div></div>`;
  }).join('');
  $('#lm-model-warnings').innerHTML = reportWarnings(report).map((warning) => `<p>${e(warning)}</p>`).join('');
  const comparison = mitigationComparison(run);
  $('#lm-mitigation-title').textContent = comparison ? (comparison.difference < 0 ? 'Lower predicted habitat loss.' : comparison.difference > 0 ? 'Higher predicted habitat loss.' : 'No change in the habitat estimate.') : 'Select options to compare.';
  $('#lm-recommendation-text').textContent = comparison ? `${Math.abs(comparison.difference).toFixed(1)} ha ${comparison.difference <= 0 ? 'less' : 'more'} predicted habitat loss${comparison.percent === null ? '' : ` (${Math.abs(comparison.percent).toFixed(0)}%)`} in the mitigation run. Both estimates use the same project type, location, scale, year, and nearby projects. Differences between medians are not a confidence interval for the mitigation effect.` : 'Choose a habitat buffer or, for industrial plants and data centres, closed-loop cooling. Run again to compare two predictions from the team’s models.';
  if (demo) {
    $('#lm-recommendation-text').textContent = comparison ? `${Math.abs(comparison.difference).toFixed(1)} ha ${comparison.difference <= 0 ? 'less' : 'more'} habitat loss${comparison.percent === null ? '' : ` (${Math.abs(comparison.percent).toFixed(0)}%)`} with the selected mitigation. Both scenarios use the same project inputs.` : 'Choose a habitat buffer or, for industrial plants and data centres, closed-loop cooling. Run again to compare the outcomes.';
    $('#lm-model-version').textContent = `Demo mode · ${report.demoVersion}. Project presets are calculated in this browser.`;
    renderIcons();
    drawAll();
    return;
  }
  $('#lm-model-sites').innerHTML = report.sites.length ? report.sites.map((site) => `<div class="lm-list-row compact"><div><div class="lm-list-name">${e(site.name)}</div><div class="lm-list-meta">${e(site.kind === 'water' ? 'Water feature' : 'Habitat')}${site.species?.length ? ` · ${e(site.species.join(', '))}` : ''}</div></div><span class="lm-pill">${Number.isFinite(site.distanceM) ? `${number(site.distanceM, 0)} m` : 'Distance unavailable'}</span></div>`).join('') : '<p class="lm-empty">No nearby features were returned from the loaded data. This does not establish that the site is ecologically clear.</p>';
  $('#lm-model-version').textContent = `Local artifact reference ${run.artifactId} · ${catalog.training.n.toLocaleString()} synthetic scenarios · ${catalog.training.split.test} held-out test cases. This evaluates imitation of the synthetic recipe, not accuracy on real projects.`;
  $('#lm-model-evaluation').innerHTML = `<table><thead><tr><th>Outcome</th><th>MAE*</th><th>Range coverage*</th><th>Cases</th></tr></thead><tbody>${outcomeDefinitions.map(({ key, label, unit, digits }) => {
    const metric = catalog.metrics.heads[key].byType[run.inputs.typeId];
    return `<tr><td>${e(label)}</td><td>${number(metric.mae, digits)} ${e(unit)}</td><td>${number(metric.coverage80 * 100, 0)}% / 80% target</td><td>${metric.n}</td></tr>`;
  }).join('')}</tbody></table><p>*Mean absolute error and p10–p90 coverage for this project type on the stored synthetic test set. A range’s target coverage is not a guarantee for this location.</p>`;
  const featureLabels = { type_idx: 'Project type', country_idx: 'Approximate country', horizon_year: 'Assessment year', min_habitat_m: 'Distance to habitat', habitat_proximity: 'Habitat proximity', habitat_hits: 'Nearby habitat features', scale: 'Project scale', buffer: 'Habitat buffer', cooling: 'Cooling', nearby_2km: 'Projects within 2 km', nearby_500m: 'Projects within 500 m', nearby_highway_2km: 'Highways within 2 km' };
  $('#lm-model-drivers').innerHTML = report.shapTop.map((item) => `<div class="lm-list-row compact"><span>${e(featureLabels[item.feature] || item.feature.replaceAll('_', ' '))}</span><span class="lm-pill">${item.value >= 0 ? '+' : ''}${number(item.value, 2)} ha</span></div>`).join('');
  renderIcons();
  drawAll();
}

export function bindSimulation() {
  $$('[data-sim-panel]').forEach((button) => button.addEventListener('click', () => showPanel(button.dataset.simPanel)));
  $('#lm-simulation-form').addEventListener('invalid', (event) => {
    showPanel('inputs');
    for (let parent = event.target.parentElement; parent && parent !== event.currentTarget; parent = parent.parentElement) {
      if (parent.tagName === 'DETAILS') parent.open = true;
    }
  }, true);
  $$('#lm-result-content details').forEach((details) => details.addEventListener('toggle', () => { if (details.open) requestAnimationFrame(drawAll); }));
  $('#lm-project-type').innerHTML = typeOptions(simulation.draft.typeId);
  $('#lm-project-location').innerHTML = locationPresets.map((item) => `<option value="${item.id}">${e(item.name)}</option>`).join('') + '<option value="custom">Custom location / map pin</option>';
  $('#lm-project-year').innerHTML = Array.from({ length: 15 }, (_, index) => `<option>${2026 + index}</option>`).join('');
  renderInputs();
  refreshSaved();
  $('#lm-simulation-form').addEventListener('input', (event) => {
    if (event.target.matches('select')) return;
    simulation.draft = readInputs();
    if (['lm-longitude', 'lm-latitude'].includes(event.target.id)) $('#lm-project-location').value = 'custom';
    markDirty();
  });
  $('#lm-simulation-form').addEventListener('change', (event) => {
    if (event.target.id === 'lm-input-mode' && event.target.value === 'scale') $('#lm-project-scale').value = simulation.draft.scale;
    if (event.target.id === 'lm-project-type') {
      measurementDrafts.set(simulation.draft.typeId, structuredClone(simulation.draft.measurements));
      const typeId = event.target.value;
      simulation.draft = { ...simulation.draft, typeId, measurements: measurementDrafts.get(typeId) || exampleMeasurements(typeId) };
      renderMeasurements();
    }
    if (event.target.id === 'lm-project-example' && event.target.value !== 'custom') {
      simulation.draft.measurements = exampleMeasurements(simulation.draft.typeId, Number(event.target.value));
      renderMeasurements();
    }
    if (event.target.matches('[data-measurement-unit]')) {
      const row = event.target.closest('[data-project-measurement]');
      const value = simulation.draft.measurements[row.dataset.projectMeasurement];
      row.querySelector('input').value = Number.isFinite(value) ? Number((value / Number(event.target.value)).toPrecision(12)) : '';
    }
    if (event.target.id === 'lm-project-location') {
      const preset = locationPresets.find((item) => item.id === event.target.value);
      if (preset) { $('#lm-longitude').value = preset.center[0]; $('#lm-latitude').value = preset.center[1]; }
    }
    if (!projectType($('#lm-project-type').value).cooling) $('#lm-cooling').checked = false;
    simulation.draft = readInputs();
    markDirty();
    if (['lm-project-location', 'lm-longitude', 'lm-latitude'].includes(event.target.id)) focusSimulation(simulation.draft.center);
  });
  $('#lm-add-nearby').addEventListener('click', () => {
    if (simulation.draft.nearbyTreatments.length >= 3) return;
    simulation.draft.nearbyTreatments.push({ typeId: 'housing', center: [...simulation.draft.center] });
    renderInputs(); markDirty();
  });
  $('#lm-nearby-projects').addEventListener('click', (event) => {
    const button = event.target.closest('[data-remove-nearby]');
    if (!button) return;
    simulation.draft.nearbyTreatments.splice(Number(button.dataset.removeNearby), 1);
    renderInputs(); markDirty();
  });
  $('#lm-pick-location').addEventListener('click', () => {
    showPanel('results');
    drawAll();
    if (!pickSimulationLocation()) { showPanel('inputs'); showError('The map is not ready. Choose a location preset or enter longitude and latitude.'); return; }
    status('Click the map to place your project.');
    $('#lm-assessment-view').scrollTo({ top: 0 });
    toast('Click the map to place your project.');
  });
  document.addEventListener('lm:project-location', (event) => {
    simulation.draft.center = event.detail.map((value) => Number(value.toFixed(6)));
    renderInputs(); markDirty(); focusSimulation(simulation.draft.center);
  });
  $$('[data-view]').forEach((button) => button.addEventListener('click', () => { simulation.view = button.dataset.view; renderResults(); }));
  $('#lm-simulation-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (state.role !== 'organisation' || simulation.running) return;
    showError();
    const input = readInputs();
    try { prepareAssessment(input); } catch (error) { showError(error.message); return; }
    simulation.draft = input;
    const current = ++requestId;
    controller = new AbortController();
    const activeController = controller;
    simulation.running = true;
    $('#lm-run').disabled = true;
    $('#lm-run span').textContent = 'Assessing…';
    status(predictionMode === 'demo' ? 'Calculating project impacts…' : 'Running the team’s impact models…');
    renderResults();
    const timeout = setTimeout(() => activeController.abort(new Error('timeout')), 45000);
    try {
      const result = await compareTreatments(input, { signal: activeController.signal });
      if (current !== requestId) return;
      simulation.lastRun = result;
      simulation.dirty = false;
      simulation.view = result.mitigated ? 'mitigated' : 'proposed';
      showPanel('results');
      $('#lm-assessment-view').scrollTo({ top: 0 });
      status(`Assessment ready · ${formatDate(result.createdAt)}`);
      toast('Assessment complete.');
    } catch (error) {
      if (current !== requestId) return;
      showPanel('inputs');
      showError(activeController.signal.aborted ? 'The model request timed out. Your previous results are preserved; please retry.' : error.message);
      status('Assessment failed · check the message above and retry.');
    } finally {
      clearTimeout(timeout);
      if (current === requestId) {
        simulation.running = false;
        controller = null;
        $('#lm-run').disabled = false;
        $('#lm-run span').textContent = 'Run assessment';
        renderResults();
      }
    }
  });
  $('#lm-save').addEventListener('click', () => {
    if (!simulation.lastRun || simulation.dirty || simulation.running) return;
    try { saveScenario({ ...simulation.lastRun, view: simulation.view }); refreshSaved(); toast('Assessment saved in this browser.'); }
    catch { showError('This assessment could not be saved. Browser storage may be unavailable or full.'); }
  });
  $('#lm-saved-scenarios').addEventListener('change', (event) => {
    const run = saved.find((item) => item.id === event.target.value);
    if (!run) return;
    stopPending();
    simulation.lastRun = structuredClone(run);
    simulation.draft = structuredClone(run.inputs);
    simulation.draft.inputMode ||= 'scale';
    simulation.draft.measurements ||= emptyMeasurements(run.inputs.typeId);
    simulation.dirty = false;
    simulation.view = run.view === 'proposed' || !run.mitigated ? 'proposed' : 'mitigated';
    showError(); renderInputs(); renderResults(); focusSimulation(run.inputs.center);
    showPanel('results');
    status(`Loaded saved results from ${formatDate(run.createdAt)}. Run again for a fresh assessment.`);
  });
}
