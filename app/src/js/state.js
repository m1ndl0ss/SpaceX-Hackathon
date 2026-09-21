export const state = {
  role: "organisation",
  profile: {
    name: "Alex Morgan",
    place: "Dordrecht",
    help: "survey",
    org: "South Holland",
    type: "municipality",
  },
  screen: "overview",
  site: 0,
  year: 2035,
  power: 80,
  water: 1200,
  land: 24,
  cooling: false,
  buffer: false,
  view: "proposed",
  incidents: true,
  overlayTheme: "habitats",
  dirty: false,
  overlays: {
    habitat: true,
    wind: true,
    grid380: true,
    grid150: true,
    gridDist: true,
    cables: true,
    substations: true,
    solar: true,
    storage: true,
    demand: true,
    incidents: true,
  },
};

export const lastRun = { ...state };
export const savedScenarios = [];

export function captureRun() {
  Object.assign(lastRun, state);
}
