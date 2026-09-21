import { overlayGroups, overlayThemes, themeHasGroup } from "../data/energy.js";
import { sites } from "../data/sites.js";
import { $, $$ } from "./dom.js";
import { state } from "./state.js";
import { drawAll, focusSite, syncLayerVisibility } from "./maps.js";
import { renderIcons } from "./icons.js";
import { applyRoleChrome } from "./community.js";

const screens = ["overview", "simulation", "people"];

export function showScreen(name) {
  if (state.role === "people" && name !== "people") name = "people";
  if (state.role === "organisation" && name === "people") name = "overview";
  state.screen = name;
  screens.forEach((id) => {
    const el = $(`#lm-${id}`);
    if (el) el.hidden = id !== name;
  });
  const labels = { overview: "Overview", simulation: "Simulation", people: "My actions" };
  const crumb = $("#lm-breadcrumb-current");
  if (crumb) crumb.textContent = labels[name] || "Overview";
  $$("[data-screen]").forEach((button) => {
    if (button.dataset.screen === name) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  applyRoleChrome();
  requestAnimationFrame(drawAll);
}

export function selectSite(index) {
  state.site = index;
  const site = sites[index];
  $("#lm-site-name").textContent = site.name;
  $("#lm-site-note").textContent = `${site.species} · Restoration opportunity`;
  $("#lm-overview .lm-map-info .lm-eyebrow").textContent = `Priority 0${index + 1} · Restoration opportunity`;
  $$("[data-site]").forEach((button) => button.classList.toggle("selected", Number(button.dataset.site) === index));
  $$("[data-action]").forEach((button) => button.classList.toggle("active", Number(button.dataset.action) === index));
  focusSite(index);
}

function overlayThemeOptions() {
  return overlayThemes
    .map(
      (theme) =>
        `<option value="${theme.id}" ${state.overlayTheme === theme.id ? "selected" : ""}>${theme.label}</option>`,
    )
    .join("");
}

function overlayMenuHtml() {
  return overlayGroups
    .map(
      (group) => `<label class="lm-layer-item" ${themeHasGroup(state.overlayTheme, group.id) ? "" : "hidden"}>
        <input type="checkbox" data-overlay="${group.id}" ${state.overlays[group.id] ? "checked" : ""}>
        <span>${group.label}</span>
      </label>`,
    )
    .join("");
}

function syncOverlayThemeUi() {
  $$("[data-overlay-theme]").forEach((select) => {
    select.value = state.overlayTheme;
  });
  $$("[data-overlay]").forEach((input) => {
    const item = input.closest(".lm-layer-item");
    if (item) item.hidden = !themeHasGroup(state.overlayTheme, input.dataset.overlay);
  });
  $$("[data-legend-set]").forEach((item) => {
    item.hidden = !item.dataset.legendSet.split(/\s+/).includes(state.overlayTheme);
  });
  syncLayerVisibility();
}

function bindLayerMenus() {
  $$("[data-overlay-theme]").forEach((select) => {
    if (!select.dataset.ready) {
      select.innerHTML = overlayThemeOptions();
      select.dataset.ready = "true";
    }
    select.addEventListener("change", () => {
      state.overlayTheme = select.value;
      syncOverlayThemeUi();
    });
  });

  $$(".lm-layer-menu").forEach((menu) => {
    if (!menu.dataset.ready) {
      menu.innerHTML = `<div class="lm-layer-title">In this set</div>${overlayMenuHtml()}`;
      menu.dataset.ready = "true";
    }
  });
  renderIcons();

  $$("[data-layer-toggle]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const menu = button.parentElement.querySelector(".lm-layer-menu");
      const open = menu.hidden;
      $$(".lm-layer-menu").forEach((other) => {
        other.hidden = true;
      });
      menu.hidden = !open;
      button.setAttribute("aria-expanded", String(open));
    });
  });

  $$("[data-overlay]").forEach((input) => {
    input.addEventListener("change", () => {
      state.overlays[input.dataset.overlay] = input.checked;
      if (input.dataset.overlay === "incidents") state.incidents = input.checked;
      $$("[data-overlay]").forEach((other) => {
        if (other.dataset.overlay === input.dataset.overlay) other.checked = input.checked;
      });
      syncLayerVisibility();
    });
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest(".lm-layer-wrap")) return;
    $$(".lm-layer-menu").forEach((menu) => {
      menu.hidden = true;
    });
    $$("[data-layer-toggle]").forEach((button) => button.setAttribute("aria-expanded", "false"));
  });

  syncOverlayThemeUi();
}

export function bindWorkspace() {
  $$("[data-screen]").forEach((button) => {
    button.addEventListener("click", () => showScreen(button.dataset.screen));
  });

  $$("[data-site]").forEach((button) => {
    button.addEventListener("click", () => selectSite(Number(button.dataset.site)));
  });
  $$("[data-action]").forEach((button) => {
    button.addEventListener("click", () => selectSite(Number(button.dataset.action)));
  });

  bindLayerMenus();
}
