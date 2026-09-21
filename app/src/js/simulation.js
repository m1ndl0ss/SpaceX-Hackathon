import { $, $$ } from "./dom.js";
import { renderIcons } from "./icons.js";
import { toast } from "./toast.js";
import { state, lastRun, savedScenarios, captureRun } from "./state.js";
import { metrics } from "./model.js";
import { drawAll } from "./maps.js";

export function renderResults() {
  const baseline = state.view === "baseline";
  const result = baseline ? { temp: 0, habitat: 0, stress: 0, price: 0 } : metrics(lastRun, state.view === "mitigated");

  $("#lm-temp").textContent = `+${result.temp.toFixed(1)}`;
  $("#lm-habitat").textContent = result.habitat ? `−${Math.round(result.habitat)}` : "0";
  $("#lm-stress").textContent = `+${Math.round(result.stress)}`;
  $("#lm-price").textContent = `+${result.price.toFixed(1)}`;
  $("#lm-temp-range").textContent = baseline
    ? "No project added"
    : `Range +${(result.temp * 0.72).toFixed(1)} to +${(result.temp * 1.28).toFixed(1)} °C`;
  $("#lm-habitat-range").textContent = baseline
    ? "No project added"
    : `Range −${Math.round(result.habitat * 0.74)} to −${Math.round(result.habitat * 1.26)} ha`;
  $("#lm-stress-range").textContent = "On a 0–100 index";
  $("#lm-price-range").textContent = baseline
    ? "No project added"
    : `Range +${(result.price * 0.7).toFixed(1)} to +${(result.price * 1.3).toFixed(1)}`;
  $("#lm-results-title").textContent = `Projected change by ${lastRun.year}`;
  $("#lm-map-year").textContent = lastRun.year;
  $("#lm-comparison-label").textContent = baseline
    ? "No project · Reference"
    : state.view === "mitigated"
      ? "Mitigated vs. no project"
      : "Proposed vs. no project";

  $$(".lm-result-val").forEach((el) => {
    el.style.color = baseline ? "var(--lm-green)" : "var(--lm-amber)";
  });

  $("#lm-impact-kicker").textContent = baseline
    ? "No-project baseline"
    : state.view === "mitigated"
      ? "Reduced impact zone"
      : "Downstream impact zone";
  $("#lm-impact-kicker").style.color =
    baseline || state.view === "mitigated" ? "var(--lm-green)" : "var(--lm-amber)";
  $("#lm-impact-copy").textContent = baseline
    ? "Reference habitat · No additional project pressure"
    : state.view === "mitigated"
      ? "Cooling + buffer · Lower thermal exposure"
      : "Thermal exposure · European eel habitat";

  const unmitigated = metrics({ ...lastRun, cooling: false, buffer: false });
  const mitigated = metrics(lastRun, true);
  $("#lm-recommendation-text").textContent =
    `Closed-loop cooling and a habitat buffer could reduce habitat loss by ${Math.round((1 - mitigated.habitat / unmitigated.habitat) * 100)}%. Cooling adds a small energy trade-off.`;

  drawAll();
}

export function setView(view) {
  state.view = view;
  $$("[data-view]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.view === view));
  });
  renderResults();
}

function markDirty() {
  state.dirty = true;
  $("#lm-save").innerHTML = '<i data-lucide="bookmark" aria-hidden="true"></i>Save scenario';
  renderIcons();
  $("#lm-input-status").textContent = "Inputs changed · Run to update results";
  $("#lm-input-status").style.color = "var(--lm-amber)";
}

export function bindSimulation() {
  for (const key of ["power", "water", "land"]) {
    $(`#lm-${key}`).addEventListener("input", (event) => {
      state[key] = Number(event.target.value);
      $("#lm-" + key + "-value").textContent =
        key === "water" ? `${state[key].toLocaleString("en")} m³/d` : `${state[key]}${key === "power" ? " MW" : " ha"}`;
      markDirty();
    });
  }

  for (const key of ["cooling", "buffer"]) {
    $(`#lm-${key}`).addEventListener("change", (event) => {
      state[key] = event.target.checked;
      markDirty();
    });
  }

  $$("[data-year]").forEach((button) => {
    button.addEventListener("click", () => {
      state.year = Number(button.dataset.year);
      $$("[data-year]").forEach((other) => other.setAttribute("aria-pressed", String(other === button)));
      markDirty();
    });
  });

  $$("[data-view]").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });

  $("#lm-apply-mitigation").addEventListener("click", () => {
    setView("mitigated");
    toast("Comparing the last run with cooling + habitat buffer");
  });

  $("#lm-run").addEventListener("click", () => {
    captureRun();
    state.dirty = false;
    $("#lm-input-status").textContent = "Scenario updated · Demo estimate";
    $("#lm-input-status").style.color = "var(--lm-green)";
    setView("proposed");
    toast("Simulation updated with your project parameters");
  });

  $("#lm-save").addEventListener("click", () => {
    if (state.dirty) {
      toast("Run the simulation before saving changed inputs");
      return;
    }
    savedScenarios.push({
      inputs: { ...lastRun },
      comparison: state.view,
      results: metrics(lastRun, state.view === "mitigated"),
    });
    $("#lm-save").innerHTML = `<i data-lucide="check" aria-hidden="true"></i>Saved · ${savedScenarios.length}`;
    renderIcons();
    toast("Scenario snapshot kept for this session");
  });
}
