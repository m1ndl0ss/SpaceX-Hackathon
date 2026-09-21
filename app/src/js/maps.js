import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import * as d3 from "d3";
import { sites } from "../data/sites.js";
import {
  cableCollection,
  demandCollection,
  feederCollection,
  grid150Collection,
  grid380Collection,
  gridDistCollection,
  overlayLayerIds,
  solarCollection,
  storageCollection,
  substationCollection,
  themeHasGroup,
  towerCollection,
  windCollection,
  windLabelCollection,
} from "../data/energy.js";
import { animalHabitatCollection, animalHabitatPoints } from "../data/habitats.js";
import { $ } from "./dom.js";
import { state, lastRun } from "./state.js";
import { svgEl } from "./svg.js";
import { metrics } from "./model.js";
import { addMapIcons } from "./map-icons.js";
import { workspace } from "./store.js";
import { isReportOpen } from "./workflow.js";

const TOKEN = String(import.meta.env.VITE_MAPBOX_TOKEN || "").trim();
const HAS_TOKEN = TOKEN.startsWith("pk.") && TOKEN.length > 40;
const BENELUX_CENTER = [5.2, 51.38];
const OVERVIEW_ZOOM = 5.45;
const SIMULATION_ZOOM = 10.35;
const INCIDENT = [4.69, 51.805];
const PROPOSED = [4.72, 51.797];
const MAP_STYLE = "mapbox://styles/mapbox/satellite-streets-v12";

const maps = {};
const markers = { overview: [], simulation: [] };

if (HAS_TOKEN) mapboxgl.accessToken = TOKEN;

function circleFeature(center, radiusKm, properties = {}) {
  const [lng, lat] = center;
  const steps = 64;
  const coords = [];
  for (let i = 0; i <= steps; i += 1) {
    const angle = (i / steps) * 2 * Math.PI;
    const dx = (radiusKm / (111.32 * Math.cos((lat * Math.PI) / 180))) * Math.cos(angle);
    const dy = (radiusKm / 110.57) * Math.sin(angle);
    coords.push([lng + dx, lat + dy]);
  }
  return {
    type: "Feature",
    properties,
    geometry: { type: "Polygon", coordinates: [coords] },
  };
}

function impactCollection() {
  if (state.view === "baseline") return { type: "FeatureCollection", features: [] };
  const impact = metrics(lastRun, state.view === "mitigated");
  const radiusKm = Math.max(0.9, Math.min(7.5, 3.6 * Math.sqrt((impact.temp / 1.8 + impact.habitat / 42) / 2)));
  return {
    type: "FeatureCollection",
    features: [circleFeature(PROPOSED, radiusKm, { view: state.view })],
  };
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function popupHtml({ kicker, title, body, meta }) {
  return `<div class="lm-popup">
    ${kicker ? `<div class="lm-popup-kicker">${escapeHtml(kicker)}</div>` : ""}
    <strong class="lm-popup-title">${escapeHtml(title)}</strong>
    ${meta ? `<div class="lm-popup-meta">${escapeHtml(meta)}</div>` : ""}
    <p>${escapeHtml(body)}</p>
  </div>`;
}

function describeFeature(layerId, props) {
  if (layerId.startsWith("habitat")) {
    return {
      kicker: props.status || "Animal habitat",
      title: props.species,
      meta: props.place,
      body: props.description,
    };
  }
  if (layerId.startsWith("wind")) {
    return {
      kicker: "Wind generation",
      title: `${props.farm} turbine`,
      meta: props.mw ? `${props.mw} MW` : "",
      body: `Turbine in the ${props.farm} cluster. Rotor sweep and night lighting overlap bird and bat routes across the North Sea and inland Benelux. Siting and shut-down windows are the main mitigation.`,
    };
  }
  if (layerId.startsWith("grid-380") || layerId === "grid-tower") {
    return {
      kicker: "380 kV transmission",
      title: props.name || "Overhead 380 kV",
      meta: "Benelux backbone · demo alignment",
      body: "Extra-high-voltage corridor moving bulk power from the North Sea and nuclear sites inland across the Netherlands, Belgium, and Luxembourg. Wide right-of-way, pylons, and collision risk for large waterbirds. Undergrounding is limited to short constrained stretches.",
    };
  }
  if (layerId.startsWith("grid-150")) {
    return {
      kicker: "150 kV grid",
      title: props.name || "150 kV line",
      meta: "Regional transmission",
      body: "Regional grid feeding substations from the Randstad through Flanders and Luxembourg. New load from industry and data centres shows up first on this layer.",
    };
  }
  if (layerId === "grid-dist") {
    return {
      kicker: "Distribution",
      title: "20 kV feeder",
      body: "Local distribution serving towns and polder pumping. These lines are easier to reroute than 150 or 380 kV, but they still cut through shoreline habitat.",
    };
  }
  if (layerId.startsWith("cable")) {
    const kind = props.kind === "underground" ? "underground cable" : props.kind === "subsea" ? "subsea export cable" : "HVDC link";
    return {
      kicker: "Cables & HVDC",
      title: props.name || kind,
      body: "Buried or subsea path that avoids new overhead pylons. Landing points and converter sites still take land, and burial can disturb sediment in shallow water.",
    };
  }
  if (layerId.startsWith("feeder")) {
    return {
      kicker: "New connection",
      title: props.name || "Project feeder",
      meta: props.kv ? `${props.kv} kV` : "",
      body: "Proposed feeder from Geertruidenberg toward the Dordrecht East data centre. This is the line that would bring the new load onto the 150 kV ring.",
    };
  }
  if (layerId.startsWith("substation")) {
    return {
      kicker: `${props.kv || ""} kV substation`.trim(),
      title: props.name,
      body: "Switchyard where transmission steps down toward local demand. Noise, security fencing, and expansion space are the usual habitat issues at the fence line.",
    };
  }
  if (layerId.startsWith("solar")) {
    return {
      kicker: "Solar park",
      title: props.name,
      body: "Ground-mounted or rooftop PV cluster. Panels shade the ground and can replace foraging habitat unless the edges stay vegetated and permeable for amphibians.",
    };
  }
  if (layerId.startsWith("storage")) {
    return {
      kicker: "Battery storage",
      title: props.name,
      body: "Grid-scale batteries sited next to a substation to soak up surplus wind. Compact footprint, but fire access and noise matter for nearby wetland.",
    };
  }
  if (layerId.startsWith("demand")) {
    return {
      kicker: props.load === "proposed" ? "Proposed demand" : "Energy demand",
      title: props.name,
      meta: props.load ? `Load: ${props.load}` : "",
      body:
        props.load === "proposed"
          ? "Dordrecht East data centre — the simulated load. Power, cooling water, and a new feeder are what show up in the habitat model."
          : "Existing industrial or logistics load on the regional grid. These sites already constrain spare capacity on the 150 kV ring.",
    };
  }
  if (layerId.startsWith("impact")) {
    return {
      kicker: "Impact zone",
      title: "Projected pressure",
      body: "Illustrative thermal and habitat footprint of the proposed data centre under the current simulation settings. Switch baseline / proposed / mitigated to compare.",
    };
  }
  return null;
}

const INTERACTIVE_LAYERS = [
  "habitat-halo",
  "habitat-fill",
  "habitat-icon",
  "wind-icon",
  "wind-halo",
  "grid-380",
  "grid-150",
  "grid-dist",
  "cable-line",
  "feeder-line",
  "substation-icon",
  "solar-fill",
  "solar-icon",
  "storage-icon",
  "demand-icon",
  "grid-tower",
  "impact-fill",
];

function bindOverlayClicks(map) {
  if (map._lmClicks) return;
  map._lmClicks = true;
  const popup = new mapboxgl.Popup({
    closeButton: true,
    closeOnClick: true,
    maxWidth: "280px",
    className: "lm-map-popup",
    offset: 18,
    anchor: "bottom",
  });

  const layers = () => INTERACTIVE_LAYERS.filter((id) => map.getLayer(id));

  map.on("click", (event) => {
    const features = map.queryRenderedFeatures(event.point, { layers: layers() });
    if (!features.length) return;
    const feature = features[0];
    const copy = describeFeature(feature.layer.id, feature.properties || {});
    if (!copy?.title) return;
    popup.setLngLat(event.lngLat).setHTML(popupHtml(copy)).addTo(map);
  });

  map.on("mousemove", (event) => {
    const hit = map.queryRenderedFeatures(event.point, { layers: layers() });
    map.getCanvas().style.cursor = hit.length ? "pointer" : "";
  });
}

function markerPopup(copy) {
  return new mapboxgl.Popup({
    closeButton: true,
    offset: 18,
    maxWidth: "280px",
    className: "lm-map-popup",
  }).setHTML(popupHtml(copy));
}

function tokenNotice(holder, message) {
  let note = holder.querySelector(".lm-map-missing");
  if (!note) {
    note = document.createElement("div");
    note.className = "lm-map-missing";
    holder.appendChild(note);
  }
  note.innerHTML = `<strong>Mapbox token needed</strong><span>${message}</span>`;
}

function addEnergyLayers(map) {
  if (map.getSource("energy-wind")) return;
  try {
    addMapIcons(map);
  } catch (error) {
    console.warn("Map icons failed", error);
  }

  const sources = {
    "energy-wind": windCollection,
    "energy-wind-labels": windLabelCollection,
    "energy-grid-380": grid380Collection,
    "energy-grid-150": grid150Collection,
    "energy-grid-dist": gridDistCollection,
    "energy-cables": cableCollection,
    "energy-towers": towerCollection,
    "energy-substations": substationCollection,
    "energy-solar": solarCollection,
    "energy-storage": storageCollection,
    "energy-demand": demandCollection,
    "energy-feeder": feederCollection,
  };
  for (const [id, data] of Object.entries(sources)) {
    map.addSource(id, { type: "geojson", data });
  }

  map.addLayer({
    id: "cable-glow",
    type: "line",
    source: "energy-cables",
    paint: { "line-color": "#7ad7c4", "line-width": 7, "line-opacity": 0.18 },
  });
  map.addLayer({
    id: "cable-line",
    type: "line",
    source: "energy-cables",
    layout: { "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color": "#8ee0c8",
      "line-width": 1.6,
      "line-dasharray": [1.1, 1.6],
      "line-opacity": 0.9,
    },
  });
  map.addLayer({
    id: "grid-380-glow",
    type: "line",
    source: "energy-grid-380",
    paint: {
      "line-color": "#f2d07a",
      "line-width": ["interpolate", ["linear"], ["zoom"], 5, 7, 9, 16],
      "line-opacity": 0.4,
    },
  });
  map.addLayer({
    id: "grid-380",
    type: "line",
    source: "energy-grid-380",
    layout: { "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color": "#ffd45c",
      "line-width": ["interpolate", ["linear"], ["zoom"], 5, 1.7, 9, 4.4],
      "line-opacity": 1,
    },
  });
  map.addLayer({
    id: "grid-380-label",
    type: "symbol",
    source: "energy-grid-380",
    minzoom: 6.8,
    layout: {
      "symbol-placement": "line",
      "text-field": ["concat", ["get", "name"], " · 380 kV"],
      "text-size": 11,
      "text-offset": [0, 0.85],
      "text-allow-overlap": false,
    },
    paint: { "text-color": "#ffe29a", "text-halo-color": "#10180f", "text-halo-width": 1.3 },
  });
  map.addLayer({
    id: "grid-150-glow",
    type: "line",
    source: "energy-grid-150",
    paint: {
      "line-color": "#5ad7e0",
      "line-width": ["interpolate", ["linear"], ["zoom"], 5, 4, 9, 10],
      "line-opacity": 0.38,
    },
  });
  map.addLayer({
    id: "grid-150",
    type: "line",
    source: "energy-grid-150",
    layout: { "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color": "#7af0f6",
      "line-width": ["interpolate", ["linear"], ["zoom"], 5, 1.2, 9, 2.8],
      "line-opacity": 1,
    },
  });
  map.addLayer({
    id: "grid-150-label",
    type: "symbol",
    source: "energy-grid-150",
    minzoom: 8.4,
    layout: {
      "symbol-placement": "line",
      "text-field": "150 kV",
      "text-size": 10,
      "text-offset": [0, 0.7],
    },
    paint: { "text-color": "#c5f4f6", "text-halo-color": "#10180f", "text-halo-width": 1.1 },
  });
  map.addLayer({
    id: "grid-dist",
    type: "line",
    source: "energy-grid-dist",
    minzoom: 9.1,
    paint: {
      "line-color": "#d5e4d3",
      "line-width": 1.25,
      "line-dasharray": [1.1, 1.3],
      "line-opacity": 0.82,
    },
  });
  map.addLayer({
    id: "feeder-glow",
    type: "line",
    source: "energy-feeder",
    paint: { "line-color": "#edb77a", "line-width": 10, "line-opacity": 0.24 },
  });
  map.addLayer({
    id: "feeder-line",
    type: "line",
    source: "energy-feeder",
    paint: {
      "line-color": "#edb77a",
      "line-width": 2.6,
      "line-dasharray": [2.2, 1.1],
    },
  });
  map.addLayer({
    id: "solar-fill",
    type: "fill",
    source: "energy-solar",
    filter: ["==", ["geometry-type"], "Polygon"],
    paint: { "fill-color": "#c9e36a", "fill-opacity": 0.32 },
  });
  map.addLayer({
    id: "solar-line",
    type: "line",
    source: "energy-solar",
    filter: ["==", ["geometry-type"], "Polygon"],
    paint: { "line-color": "#e7f59a", "line-width": 1.2 },
  });
  map.addLayer({
    id: "wind-halo",
    type: "circle",
    source: "energy-wind",
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, 6, 8, 9, 12, 16],
      "circle-color": "#7fe7ff",
      "circle-opacity": 0.55,
      "circle-stroke-color": "#f4fdff",
      "circle-stroke-width": 1.2,
      "circle-stroke-opacity": 0.9,
    },
  });
  map.addLayer({
    id: "wind-icon",
    type: "symbol",
    source: "energy-wind",
    layout: {
      "icon-image": "windmill",
      "icon-size": ["interpolate", ["linear"], ["zoom"], 5, 0.52, 8, 0.7, 12, 1.05],
      "icon-allow-overlap": true,
      "icon-ignore-placement": true,
    },
  });
  map.addLayer({
    id: "wind-label",
    type: "symbol",
    source: "energy-wind-labels",
    minzoom: 7.2,
    layout: {
      "text-field": ["get", "name"],
      "text-size": 11,
      "text-offset": [0, 1.1],
      "text-allow-overlap": false,
    },
    paint: { "text-color": "#d9f3ff", "text-halo-color": "#10180f", "text-halo-width": 1.2 },
  });
  map.addLayer({
    id: "grid-tower",
    type: "symbol",
    source: "energy-towers",
    minzoom: 9.6,
    layout: {
      "icon-image": "tower",
      "icon-size": 0.42,
      "icon-allow-overlap": true,
      "icon-ignore-placement": true,
    },
  });
  map.addLayer({
    id: "substation-icon",
    type: "symbol",
    source: "energy-substations",
    layout: {
      "icon-image": "substation",
      "icon-size": ["interpolate", ["linear"], ["zoom"], 6, 0.42, 10, 0.78],
      "icon-allow-overlap": true,
      "text-field": ["get", "name"],
      "text-size": 11,
      "text-offset": [0, 1.4],
      "text-optional": true,
    },
    paint: {
      "text-color": "#f2d07a",
      "text-halo-color": "#10180f",
      "text-halo-width": 1.2,
      "text-opacity": ["interpolate", ["linear"], ["zoom"], 7.4, 0, 8.6, 1],
    },
  });
  map.addLayer({
    id: "solar-icon",
    type: "symbol",
    source: "energy-solar",
    filter: ["==", ["geometry-type"], "Point"],
    layout: {
      "icon-image": "solar",
      "icon-size": 0.58,
      "icon-allow-overlap": true,
    },
  });
  map.addLayer({
    id: "storage-icon",
    type: "symbol",
    source: "energy-storage",
    layout: {
      "icon-image": "storage",
      "icon-size": 0.58,
      "icon-allow-overlap": true,
      "text-field": ["get", "name"],
      "text-size": 11,
      "text-offset": [0, 1.35],
      "text-optional": true,
    },
    paint: {
      "text-color": "#8ee0c8",
      "text-halo-color": "#10180f",
      "text-halo-width": 1.2,
      "text-opacity": ["interpolate", ["linear"], ["zoom"], 9.6, 0, 10.6, 1],
    },
  });
  map.addLayer({
    id: "demand-icon",
    type: "symbol",
    source: "energy-demand",
    layout: {
      "icon-image": "demand",
      "icon-size": 0.68,
      "icon-allow-overlap": true,
      "text-field": ["get", "name"],
      "text-size": 11,
      "text-offset": [0, 1.45],
      "text-optional": true,
    },
    paint: {
      "text-color": "#ffb089",
      "text-halo-color": "#10180f",
      "text-halo-width": 1.2,
      "text-opacity": ["interpolate", ["linear"], ["zoom"], 9.4, 0, 10.6, 1],
    },
  });
}

function applyOverlayVisibility(map) {
  if (!map?.getLayer("wind-icon")) return;
  for (const [group, ids] of Object.entries(overlayLayerIds)) {
    const visible = themeHasGroup(state.overlayTheme, group) && state.overlays[group] !== false;
    ids.forEach((id) => {
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
    });
  }
}

export function syncLayerVisibility() {
  Object.keys(maps).forEach((mode) => applyOverlayVisibility(maps[mode]));
  document.querySelectorAll("[data-incident]").forEach((button) => {
    const report = workspace.data.reports.find((item) => item.id === button.dataset.incident);
    button.hidden = !(report && isReportOpen(report) && themeHasGroup(state.overlayTheme, "incidents") && state.overlays.incidents);
  });
}

workspace.subscribe(syncLayerVisibility);

function addOverlayLayers(map, mode) {
  addEnergyLayers(map);

  if (!map.getSource("habitat")) {
    map.addSource("habitat", { type: "geojson", data: animalHabitatCollection });
    map.addSource("habitat-points", { type: "geojson", data: animalHabitatPoints });
    map.addLayer({
      id: "habitat-halo",
      type: "circle",
      source: "habitat-points",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, 16, 8, 22],
        "circle-color": ["coalesce", ["get", "color"], "#5dff9a"],
        "circle-opacity": 0.28,
        "circle-stroke-color": "#f4fff8",
        "circle-stroke-width": 1.4,
        "circle-stroke-opacity": 0.7,
      },
    });
    map.addLayer({
      id: "habitat-fill",
      type: "fill",
      source: "habitat",
      paint: {
        "fill-color": ["coalesce", ["get", "color"], "#5dff9a"],
        "fill-opacity": 0.5,
      },
    });
    map.addLayer({
      id: "habitat-line",
      type: "line",
      source: "habitat",
      paint: {
        "line-color": ["coalesce", ["get", "color"], "#5dff9a"],
        "line-width": ["interpolate", ["linear"], ["zoom"], 5, 2.6, 9, 2.2],
        "line-opacity": 1,
      },
    });
    map.addLayer({
      id: "habitat-icon",
      type: "symbol",
      source: "habitat-points",
      layout: {
        "icon-image": ["get", "icon"],
        "icon-size": ["interpolate", ["linear"], ["zoom"], 5, 0.62, 10, 0.82],
        "icon-allow-overlap": true,
        "icon-ignore-placement": true,
        "text-field": ["get", "species"],
        "text-size": 11,
        "text-offset": [0, 1.55],
        "text-optional": true,
        "text-allow-overlap": false,
      },
      paint: {
        "text-color": "#f4fff8",
        "text-halo-color": "#10180f",
        "text-halo-width": 1.4,
        "text-opacity": ["interpolate", ["linear"], ["zoom"], 5.6, 0, 6.6, 1],
      },
    });
  }

  if (mode === "simulation" && !map.getSource("impact")) {
    map.addSource("impact", { type: "geojson", data: impactCollection() });
    map.addLayer({
      id: "impact-fill",
      type: "fill",
      source: "impact",
      paint: { "fill-color": "#edb77a", "fill-opacity": 0.22 },
    });
    map.addLayer({
      id: "impact-line",
      type: "line",
      source: "impact",
      paint: {
        "line-color": "#edb77a",
        "line-width": 1.4,
        "line-dasharray": [2.2, 1.6],
      },
    });
  }

  applyOverlayVisibility(map);
  bindOverlayClicks(map);
}

function syncOverlays(mode) {
  const map = maps[mode];
  if (!map) return;
  applyOverlayVisibility(map);
  if (mode !== "simulation" || !map.getSource("impact")) return;

  const mitigated = state.view === "mitigated";
  map.getSource("impact").setData(impactCollection());
  map.setPaintProperty("impact-fill", "fill-color", mitigated ? "#007552" : "#edb77a");
  map.setPaintProperty("impact-fill", "fill-opacity", state.view === "baseline" ? 0 : 0.22);
  map.setPaintProperty("impact-line", "line-color", mitigated ? "#007552" : "#edb77a");
  markers.simulation.forEach((marker) => {
    marker.getElement().hidden = state.view === "baseline";
  });
}

function attachOverviewMarkers(map) {
  if (markers.overview.length) return;
  sites.forEach((site, index) => {
    const element = $(`[data-site="${index}"]`);
    if (!element) return;
    element.addEventListener("click", (event) => event.stopPropagation());
    const marker = new mapboxgl.Marker({ element, anchor: "center" }).setLngLat(site.coords).addTo(map);
    marker.setPopup(
      markerPopup({
        kicker: `Priority 0${index + 1} · ${site.species}`,
        title: site.name,
        meta: `${site.species} · Restoration opportunity`,
        body: site.text,
      }),
    );
    markers.overview.push(marker);
  });
  const incident = $("[data-incident]");
  if (incident) {
    incident.addEventListener("click", (event) => event.stopPropagation());
    markers.overview.push(new mapboxgl.Marker({ element: incident, anchor: "center" }).setLngLat(INCIDENT).addTo(map));
    incident.setAttribute("role", "button");
  }
}

function attachSimulationMarker(map) {
  if (markers.simulation.length) return;
  const element = document.createElement("div");
  element.className = "lm-proposed-site";
  element.innerHTML = "<i></i><span>Proposed site</span>";
  element.addEventListener("click", (event) => event.stopPropagation());
  const marker = new mapboxgl.Marker({ element, anchor: "bottom" }).setLngLat(PROPOSED).addTo(map);
  marker.setPopup(
    markerPopup({
      kicker: "Proposed development",
      title: "Dordrecht East data centre",
      meta: "Simulation site",
      body: "Illustrative project location on the 150 kV ring. Click habitat and grid overlays to see which species areas and feeders sit downstream of this load.",
    }),
  );
  markers.simulation.push(marker);
}

function ensureMap(mode) {
  const holder = $(`#lm-${mode}-map`);
  if (!holder || holder.offsetWidth === 0) return null;
  if (maps[mode]) {
    maps[mode].resize();
    syncOverlays(mode);
    return maps[mode];
  }
  if (!HAS_TOKEN) {
    tokenNotice(
      holder,
      "Add a real public token to <code>app/.env</code> as <code>VITE_MAPBOX_TOKEN</code>, then restart the dev server.",
    );
    return null;
  }

  holder.querySelector(".lm-map-grid")?.remove();
  holder.querySelector(".lm-map-missing")?.remove();
  if (holder.classList.contains("mapboxgl-map")) {
    holder.replaceChildren();
    holder.className = "lm-map-canvas";
  }

  const map = new mapboxgl.Map({
    container: holder,
    style: MAP_STYLE,
    center: mode === "simulation" ? PROPOSED : BENELUX_CENTER,
    zoom: mode === "simulation" ? SIMULATION_ZOOM : OVERVIEW_ZOOM,
    attributionControl: false,
    logoPosition: "bottom-left",
    fadeDuration: 0,
    pitch: mode === "simulation" ? 20 : 8,
    antialias: true,
    preserveDrawingBuffer: true,
    cooperativeGestures: false,
  });
  maps[mode] = map;
  holder._lmMap = map;

  map.on("error", (event) => {
    const status = event.error?.status;
    if (status !== 401 && status !== 403) {
      console.warn("Mapbox warning", event.error);
      return;
    }
    tokenNotice(
      holder,
      "This Mapbox token was rejected. Check it in your Mapbox account, allow localhost, and restart Vite.",
    );
  });

  let started = false;
  const onReady = () => {
    if (!map.isStyleLoaded()) return;
    if (started && map.getSource("habitat")) return;
    holder.querySelector(".lm-map-missing")?.remove();
    map.resize();
    try {
      addOverlayLayers(map, mode);
      started = true;
    } catch (error) {
      console.error("Map overlay error", error);
      return;
    }
    if (mode === "overview") attachOverviewMarkers(map);
    else attachSimulationMarker(map);
    syncOverlays(mode);
  };
  map.once("load", onReady);
  map.on("idle", onReady);
  setTimeout(onReady, 1600);

  return map;
}

export function focusSite(index) {
  const map = maps.overview;
  if (!map) return;
  map.flyTo({
    center: sites[index].coords,
    zoom: Math.max(map.getZoom(), 10.4),
    duration: 850,
    essential: true,
  });
}

export function drawMap(mode) {
  ensureMap(mode);
}

export function drawChart() {
  const svg = $("#lm-habitat-chart");
  if (!svg || svg.clientWidth === 0) return;

  const width = svg.clientWidth;
  const height = 111;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.innerHTML = "";

  const proposed = metrics(lastRun);
  const mitigated = metrics(lastRun, true);
  const years = [2026, ...[2030, 2035, 2040].filter((year) => year <= lastRun.year)];
  const values = years.map((year) => {
    const progress = (year - 2026) / (lastRun.year - 2026);
    return {
      year,
      p: 100 - (proposed.habitat / 210) * 100 * progress,
      m: 100 - (mitigated.habitat / 210) * 100 * progress,
    };
  });

  const low = Math.floor(Math.min(...values.map((value) => value.p)) / 10) * 10 - 5;
  const x = d3.scaleLinear().domain([2026, lastRun.year]).range([29, width - 8]);
  const y = d3.scaleLinear().domain([Math.min(low, 70), 103]).range([86, 11]);

  [100, Math.round((100 + Math.min(low, 70)) / 2), Math.min(low, 70)].forEach((tick) => {
    svgEl("line", { x1: 29, y1: y(tick), x2: width - 8, y2: y(tick), stroke: "rgba(0,117,82,0.16)", "stroke-width": 0.5 }, svg);
    const label = svgEl("text", { x: 22, y: y(tick) + 3, fill: "#5a7a70", "font-size": 11, "text-anchor": "end", "font-family": "Michroma, sans-serif" }, svg);
    label.textContent = tick;
  });

  [2026, Math.round((2026 + lastRun.year) / 2), lastRun.year].forEach((tick) => {
    const anchor = tick === 2026 ? "start" : tick === lastRun.year ? "end" : "middle";
    const label = svgEl("text", { x: x(tick), y: 104, fill: "#5a7a70", "font-size": 11, "text-anchor": anchor, "font-family": "Michroma, sans-serif" }, svg);
    label.textContent = tick;
  });

  const line = (key) =>
    d3
      .line()
      .x((d) => x(d.year))
      .y((d) => y(d[key]))
      .curve(d3.curveMonotoneX)(values);

  svgEl(
    "path",
    {
      d: `${line("p")}L${x(lastRun.year)},${y(Math.min(low, 70))}L${x(2026)},${y(Math.min(low, 70))}Z`,
      fill: "rgba(201,132,42,0.08)",
    },
    svg,
  );
  svgEl("path", { d: line("p"), fill: "none", stroke: "#c9842a", "stroke-width": 1.8 }, svg);
  svgEl("path", { d: line("m"), fill: "none", stroke: "#007552", "stroke-width": 1.8 }, svg);

  for (const key of ["p", "m"]) {
    const last = values.at(-1);
    svgEl(
      "circle",
      {
        cx: x(last.year),
        cy: y(last[key]),
        r: 2.5,
        fill: key === "p" ? "#c9842a" : "#007552",
      },
      svg,
    );
  }
}

export function drawAll() {
  drawMap("overview");
  drawMap("simulation");
  drawChart();
}
