const point = (coordinates, properties = {}) => ({
  type: "Feature",
  properties,
  geometry: { type: "Point", coordinates },
});

const line = (coordinates, properties = {}) => ({
  type: "Feature",
  properties,
  geometry: { type: "LineString", coordinates },
});

const polygon = (ring, properties = {}) => ({
  type: "Feature",
  properties,
  geometry: { type: "Polygon", coordinates: [ring] },
});

function turbines(origin, count, farm, spacing = [0.016, 0.011]) {
  const features = [];
  for (let i = 0; i < count; i += 1) {
    const col = i % 6;
    const row = Math.floor(i / 6);
    const wobble = ((i * 13) % 5) * 0.0018;
    features.push(
      point(
        [origin[0] + col * spacing[0] + wobble, origin[1] - row * spacing[1] - wobble * 0.4],
        { kind: "wind", farm, mw: 3.6 + (i % 4) * 0.6 },
      ),
    );
  }
  return features;
}

function closedRing(origin, w, h) {
  const [x, y] = origin;
  return [
    [x, y],
    [x + w, y],
    [x + w, y + h],
    [x, y + h],
    [x, y],
  ];
}

function towersAlong(coords, kv) {
  const features = [];
  for (let i = 0; i < coords.length - 1; i += 1) {
    const a = coords[i];
    const b = coords[i + 1];
    const dist = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const steps = Math.max(1, Math.round(dist / 0.08));
    for (let j = 1; j < steps; j += 1) {
      const t = j / steps;
      features.push(point([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t], { kv }));
    }
  }
  return features;
}

const grid380Lines = [
  [
    [4.02, 51.956],
    [4.28, 51.905],
    [4.29, 51.825],
    [4.48, 51.818],
    [4.705, 51.812],
    [4.83, 51.701],
  ],
  [
    [4.83, 51.701],
    [5.12, 51.55],
    [5.47, 51.44],
    [5.89, 51.14],
  ],
  [
    [4.02, 51.956],
    [4.55, 52.2],
    [4.96, 52.34],
    [5.12, 52.09],
    [5.48, 52.18],
  ],
  [
    [4.96, 52.34],
    [5.8, 52.7],
    [6.57, 53.22],
    [6.83, 53.44],
  ],
  [
    [4.83, 51.701],
    [5.65, 51.92],
    [6.29, 51.97],
    [6.1, 51.45],
    [5.89, 51.14],
  ],
  [
    [3.73, 51.43],
    [3.96, 51.55],
    [4.29, 51.825],
  ],
  [
    [4.27, 51.32],
    [4.4, 51.2],
    [4.48, 51.03],
    [4.35, 50.85],
    [4.44, 50.41],
  ],
  [
    [3.2, 51.33],
    [3.45, 50.78],
    [4.35, 50.85],
  ],
  [
    [4.27, 51.32],
    [4.83, 51.701],
  ],
  [
    [4.35, 50.85],
    [4.87, 50.47],
    [5.53, 50.59],
    [5.82, 49.57],
    [6.0, 49.51],
    [6.13, 49.61],
  ],
  [
    [5.89, 51.14],
    [5.74, 51.15],
    [5.53, 50.59],
  ],
  [
    [3.73, 51.43],
    [3.72, 51.05],
    [4.27, 51.32],
  ],
];

export const overlayGroups = [
  { id: "habitat", label: "Animal habitats" },
  { id: "wind", label: "Wind turbines" },
  { id: "grid380", label: "380 kV grid" },
  { id: "grid150", label: "150 kV grid" },
  { id: "gridDist", label: "Distribution" },
  { id: "cables", label: "Cables & HVDC" },
  { id: "substations", label: "Substations" },
  { id: "solar", label: "Solar parks" },
  { id: "storage", label: "Storage" },
  { id: "demand", label: "Energy demand" },
  { id: "incidents", label: "Field reports" },
];

export const overlayThemes = [
  { id: "habitats", label: "Habitats", groups: ["habitat", "incidents"] },
  { id: "energy", label: "Energy", groups: ["wind", "solar", "storage", "demand"] },
  { id: "grid", label: "Grid", groups: ["grid380", "grid150", "gridDist", "cables", "substations"] },
  { id: "all", label: "All layers", groups: null },
];

export function themeHasGroup(themeId, groupId) {
  const theme = overlayThemes.find((item) => item.id === themeId) ?? overlayThemes[0];
  return !theme.groups || theme.groups.includes(groupId);
}

export const overlayLayerIds = {
  habitat: ["habitat-halo", "habitat-fill", "habitat-line", "habitat-icon"],
  wind: ["wind-halo", "wind-icon", "wind-label"],
  grid380: ["grid-380-glow", "grid-380", "grid-380-label", "grid-tower"],
  grid150: ["grid-150-glow", "grid-150", "grid-150-label"],
  gridDist: ["grid-dist"],
  cables: ["cable-glow", "cable-line"],
  substations: ["substation-icon"],
  solar: ["solar-fill", "solar-line", "solar-icon"],
  storage: ["storage-icon"],
  demand: ["demand-icon", "feeder-glow", "feeder-line"],
};

export const windCollection = {
  type: "FeatureCollection",
  features: [
    ...turbines([3.99, 51.955], 12, "Maasvlakte"),
    ...turbines([3.93, 51.742], 8, "Goeree"),
    ...turbines([4.12, 51.772], 8, "Haringvliet"),
    ...turbines([4.46, 51.738], 6, "Hoeksche Waard"),
    ...turbines([3.15, 51.65], 14, "Borssele offshore", [0.022, 0.016]),
    ...turbines([4.05, 52.28], 14, "Hollandse Kust Zuid", [0.024, 0.016]),
    ...turbines([4.18, 52.58], 12, "Hollandse Kust Noord", [0.024, 0.016]),
    ...turbines([5.55, 52.55], 10, "Flevoland", [0.02, 0.014]),
    ...turbines([6.75, 53.38], 10, "Eemshaven", [0.02, 0.014]),
    ...turbines([5.9, 53.18], 8, "Fryslân", [0.018, 0.013]),
    ...turbines([6.15, 52.48], 6, "Zwolle", [0.016, 0.012]),
    ...turbines([5.7, 51.95], 6, "Betuwe", [0.016, 0.012]),
    ...turbines([2.93, 51.55], 12, "Thornton Bank", [0.022, 0.015]),
    ...turbines([3.02, 51.52], 10, "Norther", [0.02, 0.014]),
    ...turbines([2.88, 51.64], 8, "Belwind", [0.02, 0.014]),
    ...turbines([3.35, 51.12], 8, "Flanders coast", [0.018, 0.012]),
    ...turbines([4.55, 51.12], 8, "Antwerp harbour", [0.016, 0.012]),
    ...turbines([5.35, 50.72], 8, "Liège plateau", [0.018, 0.012]),
    ...turbines([4.22, 50.38], 8, "Hainaut", [0.018, 0.012]),
    ...turbines([5.05, 50.05], 6, "Namur ridges", [0.016, 0.012]),
    ...turbines([5.95, 49.72], 6, "Luxembourg north", [0.014, 0.01]),
    ...turbines([6.05, 49.52], 4, "Minett", [0.012, 0.01]),
  ],
};

export const windLabelCollection = {
  type: "FeatureCollection",
  features: [
    point([3.2, 51.64], { name: "Borssele / Thornton" }),
    point([4.1, 52.35], { name: "Hollandse Kust" }),
    point([4.04, 51.948], { name: "Maasvlakte wind" }),
    point([5.55, 52.54], { name: "Flevoland wind" }),
    point([6.75, 53.38], { name: "Eemshaven wind" }),
    point([3.35, 51.12], { name: "Flanders wind" }),
    point([5.35, 50.72], { name: "Liège wind" }),
    point([5.95, 49.72], { name: "Éislek wind" }),
  ],
};

export const grid380Collection = {
  type: "FeatureCollection",
  features: [
    line(grid380Lines[0], { name: "Maasvlakte–Geertruidenberg", kv: 380 }),
    line(grid380Lines[1], { name: "Brabant backbone", kv: 380 }),
    line(grid380Lines[2], { name: "Randstad 380 kV", kv: 380 }),
    line(grid380Lines[3], { name: "North Holland–Eemshaven", kv: 380 }),
    line(grid380Lines[4], { name: "Doetinchem–Maasbracht", kv: 380 }),
    line(grid380Lines[5], { name: "Borssele–Simonshaven", kv: 380 }),
    line(grid380Lines[6], { name: "Doel–Brussels–Charleroi", kv: 380 }),
    line(grid380Lines[7], { name: "Stevin–Mercator", kv: 380 }),
    line(grid380Lines[8], { name: "Zandvliet–Geertruidenberg", kv: 380 }),
    line(grid380Lines[9], { name: "Gramme–Luxembourg", kv: 380 }),
    line(grid380Lines[10], { name: "Van Eyck–Gramme", kv: 380 }),
    line(grid380Lines[11], { name: "Borssele–Doel", kv: 380 }),
  ],
};

export const towerCollection = {
  type: "FeatureCollection",
  features: grid380Lines.flatMap((coords) => towersAlong(coords, 380)),
};

export const grid150Collection = {
  type: "FeatureCollection",
  features: [
    line([[4.705, 51.812], [4.69, 51.82], [4.72, 51.797], [4.75, 51.78], [4.83, 51.701]], { name: "Dordrecht ring", kv: 150 }),
    line([[4.29, 51.825], [4.36, 51.84], [4.45, 51.835], [4.58, 51.828], [4.66, 51.82], [4.705, 51.812]], { name: "Oude Maas 150 kV", kv: 150 }),
    line([[4.28, 51.905], [4.4, 51.9], [4.55, 51.89], [4.67, 51.86], [4.705, 51.812]], { name: "Rotterdam–Dordrecht 150 kV", kv: 150 }),
    line([[4.12, 51.772], [4.22, 51.79], [4.32, 51.8], [4.29, 51.825]], { name: "Haringvliet collector", kv: 150 }),
    line([[4.96, 52.34], [5.12, 52.09], [5.18, 51.98], [5.47, 51.44]], { name: "Utrecht–Eindhoven 150 kV", kv: 150 }),
    line([[6.83, 53.44], [6.57, 53.22], [6.09, 52.51], [5.48, 52.52]], { name: "North 150 kV", kv: 150 }),
    line([[4.27, 51.32], [4.4, 51.22], [4.48, 51.03], [4.35, 50.85]], { name: "Antwerp–Brussels 150 kV", kv: 150 }),
    line([[3.72, 51.05], [4.0, 51.0], [4.27, 51.32]], { name: "Ghent–Antwerp 150 kV", kv: 150 }),
    line([[4.35, 50.85], [4.6, 50.7], [5.0, 50.64], [5.53, 50.59]], { name: "Brussels–Liège 150 kV", kv: 150 }),
    line([[5.82, 49.57], [6.0, 49.51], [6.13, 49.61], [6.16, 49.93]], { name: "Luxembourg 220/150 kV ring", kv: 150 }),
    line([[4.44, 50.41], [4.7, 50.2], [5.05, 50.05], [5.53, 50.59]], { name: "Sambre–Meuse 150 kV", kv: 150 }),
    line([[5.47, 51.44], [5.74, 51.15], [5.89, 51.14]], { name: "Campine 150 kV", kv: 150 }),
  ],
};

export const gridDistCollection = {
  type: "FeatureCollection",
  features: [
    line([[4.72, 51.797], [4.74, 51.805], [4.76, 51.81], [4.78, 51.806]], { kv: 20 }),
    line([[4.72, 51.797], [4.7, 51.79], [4.68, 51.784], [4.66, 51.78]], { kv: 20 }),
    line([[4.67, 51.813], [4.65, 51.808], [4.63, 51.8], [4.61, 51.795]], { kv: 20 }),
    line([[4.49, 51.826], [4.52, 51.83], [4.55, 51.828], [4.58, 51.822]], { kv: 20 }),
    line([[4.22, 51.77], [4.25, 51.778], [4.28, 51.79], [4.3, 51.808]], { kv: 20 }),
    line([[4.77, 51.755], [4.79, 51.762], [4.8, 51.772], [4.81, 51.78]], { kv: 20 }),
    line([[4.35, 50.85], [4.38, 50.86], [4.42, 50.87]], { kv: 20 }),
    line([[4.27, 51.32], [4.3, 51.3], [4.33, 51.28]], { kv: 20 }),
    line([[6.13, 49.61], [6.16, 49.62], [6.2, 49.63]], { kv: 20 }),
    line([[3.72, 51.05], [3.75, 51.06], [3.78, 51.07]], { kv: 20 }),
    line([[4.96, 52.34], [4.99, 52.35], [5.03, 52.36]], { kv: 20 }),
    line([[5.53, 50.59], [5.56, 50.6], [5.6, 50.61]], { kv: 20 }),
  ],
};

export const cableCollection = {
  type: "FeatureCollection",
  features: [
    line([[3.96, 51.745], [3.88, 51.78], [3.9, 51.84], [3.97, 51.91], [4.02, 51.956]], { name: "Goeree–Maasvlakte HVDC", kind: "hvdc" }),
    line([[4.02, 51.956], [3.7, 52.15], [3.4, 52.4], [3.1, 52.7]], { name: "BritNed", kind: "subsea" }),
    line([[3.2, 51.33], [2.7, 51.4], [2.2, 51.45], [1.7, 51.4]], { name: "Nemo Link", kind: "hvdc" }),
    line([[6.83, 53.44], [6.4, 53.7], [5.8, 54.0], [5.2, 54.2]], { name: "NorNed / COBRAcable", kind: "subsea" }),
    line([[5.53, 50.59], [5.9, 50.7], [6.2, 50.78], [6.5, 50.85]], { name: "ALEGrO", kind: "hvdc" }),
    line([[3.15, 51.65], [3.4, 51.55], [3.73, 51.43]], { name: "Borssele export cable", kind: "subsea" }),
    line([[2.93, 51.55], [3.05, 51.45], [3.2, 51.33]], { name: "Thornton landing", kind: "subsea" }),
    line([[4.29, 51.825], [4.42, 51.8], [4.62, 51.796], [4.72, 51.797]], { name: "Oude Maas underground", kind: "underground" }),
    line([[4.35, 50.85], [4.4, 50.86], [4.48, 51.03]], { name: "Brussels north cable", kind: "underground" }),
  ],
};

export const substationCollection = {
  type: "FeatureCollection",
  features: [
    point([4.83, 51.701], { name: "Geertruidenberg", kv: 380 }),
    point([4.705, 51.812], { name: "Crayestein", kv: 380 }),
    point([4.29, 51.825], { name: "Simonshaven", kv: 380 }),
    point([4.02, 51.956], { name: "Maasvlakte", kv: 380 }),
    point([3.73, 51.43], { name: "Borssele", kv: 380 }),
    point([4.96, 52.34], { name: "Diemen", kv: 380 }),
    point([6.83, 53.44], { name: "Eemshaven", kv: 380 }),
    point([5.89, 51.14], { name: "Maasbracht", kv: 380 }),
    point([6.29, 51.97], { name: "Doetinchem", kv: 380 }),
    point([4.27, 51.32], { name: "Doel / Zandvliet", kv: 380 }),
    point([4.35, 50.85], { name: "Bruegel", kv: 380 }),
    point([5.53, 50.59], { name: "Gramme", kv: 380 }),
    point([3.2, 51.33], { name: "Stevin", kv: 380 }),
    point([3.45, 50.78], { name: "Avelgem", kv: 380 }),
    point([5.74, 51.15], { name: "Van Eyck", kv: 380 }),
    point([6.0, 49.51], { name: "Schifflange", kv: 220 }),
    point([6.13, 49.61], { name: "Heisdorf", kv: 220 }),
    point([6.16, 49.93], { name: "Vianden", kv: 220 }),
    point([4.628, 51.701], { name: "Moerdijk", kv: 150 }),
    point([4.66, 51.82], { name: "Dordrecht", kv: 150 }),
    point([3.72, 51.05], { name: "Ghent", kv: 150 }),
    point([5.47, 51.44], { name: "Eindhoven", kv: 150 }),
  ],
};

export const solarCollection = {
  type: "FeatureCollection",
  features: [
    polygon(closedRing([4.58, 51.678], 0.08, 0.032), { name: "Moerdijk solar" }),
    polygon(closedRing([4.4, 51.722], 0.07, 0.026), { name: "Hoeksche Waard solar" }),
    polygon(closedRing([4.08, 51.9], 0.055, 0.022), { name: "Botlek rooftop cluster" }),
    polygon(closedRing([5.42, 52.48], 0.09, 0.04), { name: "Flevoland solar" }),
    polygon(closedRing([6.05, 53.1], 0.08, 0.03), { name: "Groningen solar" }),
    polygon(closedRing([5.55, 51.48], 0.07, 0.028), { name: "North Brabant solar" }),
    polygon(closedRing([4.95, 51.55], 0.06, 0.024), { name: "Kempen solar" }),
    polygon(closedRing([3.55, 50.95], 0.085, 0.032), { name: "East Flanders solar" }),
    polygon(closedRing([5.2, 50.85], 0.07, 0.03), { name: "Limburg BE solar" }),
    polygon(closedRing([4.5, 50.45], 0.075, 0.03), { name: "Hainaut solar" }),
    polygon(closedRing([5.95, 49.58], 0.05, 0.022), { name: "Minett rooftop cluster" }),
    polygon(closedRing([6.2, 49.75], 0.045, 0.02), { name: "Ösling solar" }),
    point([4.605, 51.688], { name: "Moerdijk solar" }),
    point([5.46, 52.5], { name: "Flevoland solar" }),
    point([3.59, 50.96], { name: "East Flanders solar" }),
    point([5.98, 49.59], { name: "Minett solar" }),
    point([6.08, 53.11], { name: "Groningen solar" }),
    point([4.54, 50.46], { name: "Hainaut solar" }),
  ],
};

export const storageCollection = {
  type: "FeatureCollection",
  features: [
    point([4.71, 51.804], { name: "Crayestein BESS" }),
    point([4.04, 51.948], { name: "Maasvlakte storage" }),
    point([4.62, 51.696], { name: "Moerdijk BESS" }),
    point([6.83, 53.43], { name: "Eemshaven BESS" }),
    point([3.73, 51.43], { name: "Borssele storage" }),
    point([5.48, 52.52], { name: "Lelystad BESS" }),
    point([4.27, 51.31], { name: "Doel storage" }),
    point([4.36, 50.86], { name: "Brussels BESS" }),
    point([5.53, 50.6], { name: "Gramme storage" }),
    point([6.16, 49.93], { name: "Vianden PSP" }),
    point([6.0, 49.52], { name: "Schifflange BESS" }),
  ],
};

export const demandCollection = {
  type: "FeatureCollection",
  features: [
    point([4.27, 51.898], { name: "Botlek industry", load: "high" }),
    point([4.62, 51.688], { name: "Moerdijk chemie", load: "high" }),
    point([4.72, 51.797], { name: "Dordrecht East data centre", load: "proposed" }),
    point([4.04, 51.95], { name: "Maasvlakte port", load: "high" }),
    point([4.9, 52.37], { name: "Amsterdam data centres", load: "high" }),
    point([5.48, 51.44], { name: "Eindhoven Brainport", load: "high" }),
    point([6.57, 53.22], { name: "Groningen industry", load: "medium" }),
    point([4.4, 51.22], { name: "Port of Antwerp", load: "high" }),
    point([4.35, 50.85], { name: "Brussels metro", load: "high" }),
    point([3.72, 51.05], { name: "Ghent industry", load: "high" }),
    point([5.57, 50.64], { name: "Liège steel", load: "high" }),
    point([4.44, 50.41], { name: "Charleroi", load: "medium" }),
    point([6.13, 49.61], { name: "Luxembourg City", load: "high" }),
    point([6.01, 49.5], { name: "Belval / Esch", load: "medium" }),
  ],
};

export const feederCollection = {
  type: "FeatureCollection",
  features: [
    line([[4.83, 51.701], [4.78, 51.74], [4.74, 51.77], [4.72, 51.797]], { name: "New 150 kV feeder", kv: 150 }),
    line([[4.96, 52.34], [5.05, 52.38], [5.12, 52.42]], { name: "Amsterdam east feeder", kv: 150 }),
    line([[4.27, 51.32], [4.35, 51.28], [4.42, 51.24]], { name: "Antwerp port feeder", kv: 150 }),
    line([[6.0, 49.51], [6.06, 49.55], [6.13, 49.61]], { name: "Minett–city feeder", kv: 150 }),
  ],
};

