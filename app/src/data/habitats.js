function ellipseRing(center, kmX, kmY, rotation = 0, steps = 48) {
  const [lng, lat] = center;
  const cosLat = Math.cos((lat * Math.PI) / 180);
  const coords = [];
  for (let i = 0; i <= steps; i += 1) {
    const angle = (i / steps) * 2 * Math.PI + rotation;
    const dx = (kmX * Math.cos(angle)) / (111.32 * cosLat);
    const dy = (kmY * Math.sin(angle)) / 110.57;
    coords.push([lng + dx, lat + dy]);
  }
  return coords;
}

const habitat = (center, kmX, kmY, rotation, properties) => ({
  type: "Feature",
  properties: { ...properties, center },
  geometry: { type: "Polygon", coordinates: [ellipseRing(center, kmX, kmY, rotation)] },
});

const patches = [
  [[4.77, 51.755], 16, 10, 0.35, "European eel", "Biesbosch wetlands", "eel", "#5dff9a", "Critically declining", "Glass eels still use the Biesbosch channels as a nursery. Reconnecting tidal creeks is the priority action here."],
  [[4.2, 51.77], 18, 9, -0.2, "Eurasian spoonbill", "Haringvliet shoreline", "bird", "#7ef0ff", "Breeding colony", "Shallow shoreline feeds spoonbill and migratory geese. A quiet buffer along the banks keeps the colony viable."],
  [[4.68, 51.78], 10, 7, 0.5, "Eurasian beaver", "Biesbosch willow coppice", "beaver", "#ffe07a", "Re-established", "Beavers have returned to willow coppice west of Dordrecht. Connected wet woodland lets them dam without being treated only as flood risk."],
  [[4.05, 51.74], 14, 8, 0.15, "Harbour seal", "Haringvliet mouth", "seal", "#9ab8ff", "Haul-out site", "Seals haul out on sandbanks where the Haringvliet meets the North Sea. A wider quiet zone at low tide keeps the site open."],
  [[4.49, 51.826], 12, 7, 1.1, "Riparian songbirds", "Oude Maas corridor", "bird", "#4dffb0", "Fragmented", "Reed warbler and nightingale use remaining riverbank scrub. Native planting that joins existing woods repairs the corridor."],
  [[4.62, 51.7], 12, 7, 0.05, "Northern pike", "Hollands Diep shallows", "fish", "#6dffc4", "Spawning habitat", "Pike spawn in vegetated shallows along the Diep. Cooler inflows and a wider reed margin keep recruitment going."],
  [[4.12, 51.86], 9, 6, 0.7, "Natterjack toad", "Voorne dunes", "toad", "#ffb06a", "Locally rare", "Natterjacks breed in warm dune pools on Voorne. Scraping a few ephemeral pans each spring keeps a breeding foothold."],
  [[5.4, 53.28], 42, 16, 0.12, "Harbour seal", "Wadden Sea", "seal", "#8eb4ff", "World Heritage haul-out", "The Wadden Sea is the core haul-out for harbour seals in the north. Wide quiet zones on the sandbanks are the main conservation lever."],
  [[5.35, 52.72], 28, 16, 0.05, "Pike-perch", "IJsselmeer", "fish", "#5ee8ff", "Open-water nursery", "IJsselmeer still supports pike-perch and the birds that feed on the same shallows. Softer reed edges restore the food web."],
  [[5.85, 52.18], 24, 16, 0.4, "Black grouse", "Veluwe heath", "bird", "#e6c46a", "Isolated population", "Heath and drift sand on the Veluwe still hold a thin grouse population. Grazing and quiet core zones keep the last leks viable."],
  [[6.55, 53.35], 18, 11, -0.25, "European eel", "Eems–Dollard", "eel", "#5dffb0", "Estuary nursery", "Muddy nursery for eel and flounder on the German–Dutch border. Restoring soft mudflats gives glass eels a place to feed."],
  [[3.42, 51.34], 20, 11, 0.2, "Migratory geese", "Zwin and Scheldt", "bird", "#7ee8c8", "Flyway stopover", "Mudflats here are a North Sea flyway stop. Timed access and restored saltmarsh keep the stopover intact."],
  [[4.15, 51.18], 18, 12, 0.55, "European eel", "Scheldt freshwater reach", "eel", "#4dff9a", "Migration bottleneck", "Eels stall below Antwerp at locks and pumps. Fish-friendly pumping reopens the corridor into Flanders."],
  [[5.15, 51.22], 22, 15, 0.15, "Natterjack toad", "Kempen heath", "toad", "#ffb56a", "Heathland remnant", "Natterjacks and nightjars use remaining Campine heath. Opening a few wet heath cores keeps the amphibian foothold."],
  [[3.55, 51.08], 16, 10, 0.3, "Riparian songbirds", "Lys valley", "bird", "#5ee89a", "Farmland edge", "Reed and willow along the Lys still carry warblers through Flanders. Native buffers reconnect the corridor."],
  [[4.72, 50.52], 20, 12, 0.1, "Northern pike", "Sambre wetlands", "fish", "#6ee8b0", "Spawning habitat", "Pike use leftover wetlands along the Sambre. Reconnecting oxbows restores a working floodplain."],
  [[5.55, 50.18], 30, 18, 0.55, "Eurasian beaver", "Ardennes rivers", "beaver", "#ffd56a", "Expanding", "Beavers have recolonised the Ourthe and Semois. Woody banks and room to dam also shelter otter and lynx prey."],
  [[6.12, 50.52], 16, 11, -0.2, "Black grouse", "Hautes Fagnes", "bird", "#c8e86a", "Peat bog remnant", "Peat and spruce edge still hold grouse. Blocking ditches and a quiet nesting core is the restoration path."],
  [[5.95, 49.82], 15, 10, 0.35, "Eurasian beaver", "Our and Sûre valleys", "beaver", "#ffd07a", "Riverine woodland", "Otter and beaver use the Our through northern Luxembourg. Fish passes and woody buffers keep the valley connected."],
  [[6.18, 49.58], 11, 8, 0.8, "Natterjack toad", "Minett former mines", "toad", "#ff9e6a", "Industrial habitat", "Warm pools on former iron-ore terraces still hold natterjacks. Keeping a few unshaded scrapes in land-reuse plans preserves this foothold."],
  [[4.78, 53.08], 16, 10, 0.2, "Harbour seal", "Texel and Marsdiep", "seal", "#9ec4ff", "Coastal haul-out", "Demo overlay for seals and dune birds on Texel. Quiet beaches at pupping time keep the haul-out in use."],
  [[5.15, 53.05], 14, 9, -0.4, "Migratory geese", "Frisian lakes", "bird", "#7affd0", "Wintering flocks", "Illustrative geese and wigeon habitat on the Frisian lake plateau. Wet grassland buffers keep roosts linked to feeding fields."],
  [[6.05, 53.05], 15, 10, 0.25, "European eel", "Groningen peat canals", "eel", "#62ffb4", "Peat nursery", "Demo eel and stickleback habitat in rewetted peat. Raising summer water in a few polders reconnects the ditches."],
  [[6.55, 52.85], 14, 10, 0.6, "Natterjack toad", "Drenthe heath", "toad", "#ffc06a", "Heath remnant", "Illustrative natterjack and adder habitat on Drenthe heath. Open sand and wet pans keep the mosaic working."],
  [[5.95, 52.7], 16, 11, 0.1, "Northern pike", "Weerribben–Wieden", "fish", "#5cffd8", "Fen fishery", "Demo pike and otter habitat in the Weerribben fens. Open reed and turf ponds keep spawning bays intact."],
  [[5.2, 52.55], 14, 9, 0.45, "Riparian songbirds", "Waterland peat", "bird", "#6affb0", "Peat meadow", "Illustrative songbird and lapwing habitat north of Amsterdam. High water in spring keeps nests off the plough."],
  [[4.62, 52.42], 13, 8, -0.2, "Natterjack toad", "Kennemer dunes", "toad", "#ffb87a", "Dune pools", "Demo toad and dune-bird habitat in the Kennemer belt. Scraped slacks keep warm breeding pans after wet winters."],
  [[4.55, 52.15], 12, 8, 0.55, "Riparian songbirds", "Green Heart peat", "bird", "#58e89a", "Peat polder", "Illustrative meadow-bird overlay between Leiden and Utrecht. Raised ditches and delayed mowing hold a breeding patch."],
  [[5.35, 52.08], 14, 10, 0.3, "Black grouse", "Utrechtse Heuvelrug", "bird", "#e8d06a", "Ridge forest", "Demo grouse and badger habitat on the Utrecht ridge. Open heath pockets inside the pine keep a mosaic."],
  [[6.05, 52.25], 13, 9, -0.35, "Eurasian beaver", "IJssel floodplain", "beaver", "#ffdc7a", "River woodland", "Illustrative beaver and stork habitat along the IJssel. Side channels and willow give them room to dam."],
  [[5.95, 51.88], 15, 10, 0.2, "European eel", "Gelderse Poort", "eel", "#4dffb8", "River junction", "Demo eel and beaver habitat where Rhine and Waal split. Reconnected oxbows keep the junction wet."],
  [[6.45, 52.15], 13, 9, 0.7, "Natterjack toad", "Twente heath", "toad", "#ffae6a", "Sandy heath", "Illustrative toad and nightjar habitat in Twente. Open drift sand after grazing keeps pans warm."],
  [[6.55, 51.95], 12, 8, 0.15, "Riparian songbirds", "Achterhoek streams", "bird", "#6ee8a0", "Brook valley", "Demo songbird overlay on Achterhoek brooks. Woody buffers on the last meanders reconnect the valley."],
  [[5.85, 51.62], 14, 10, 0.5, "Northern pike", "Maas floodplain", "fish", "#5ce8c4", "Flood meadow", "Illustrative pike habitat on the Maas between Cuijk and Venlo. Seasonal flooding of a few meadows restores spawning."],
  [[5.95, 51.42], 13, 9, -0.15, "Eurasian beaver", "Maasduinen", "beaver", "#ffe08a", "River dunes", "Demo beaver and nightjar habitat in the Maasduinen. Wet dune slacks and woody banks keep both species."],
  [[5.85, 50.88], 12, 8, 0.4, "Riparian songbirds", "Mergelland", "bird", "#7affb4", "Chalk grassland", "Illustrative songbird and hamster habitat in South Limburg. Flower-rich banks and orchards hold the overlay."],
  [[4.78, 51.52], 13, 9, 0.25, "Natterjack toad", "Brabant sands", "toad", "#ffc46a", "Cover sand", "Demo toad and woodlark habitat on North Brabant sands. Open heath after pine removal keeps pans."],
  [[3.85, 51.48], 14, 8, -0.3, "Harbour seal", "Eastern Scheldt", "seal", "#8eb8ff", "Tidal banks", "Illustrative seal and oystercatcher habitat in the Eastern Scheldt. Quiet plates at low tide keep haul-outs."],
  [[3.55, 51.52], 12, 7, 0.6, "Migratory geese", "Zeeland dunes", "bird", "#7affdc", "Coastal dune", "Demo geese and frog habitat behind the Zeeland dunes. Wet slacks after storms hold a breeding patch."],
  [[2.95, 51.22], 14, 8, 0.1, "Harbour seal", "Flanders coast", "seal", "#9ac4ff", "Beach haul-out", "Illustrative seal and dune-toad habitat on the Belgian coast. Timed access on a few beaches keeps the overlay."],
  [[3.25, 50.95], 13, 9, 0.45, "Northern pike", "Meetjesland creeks", "fish", "#5cffc8", "Creek fishery", "Demo pike habitat in East Flanders creeks. Reconnecting a polder ditch restores spawning."],
  [[3.85, 50.85], 14, 10, -0.2, "Riparian songbirds", "Scheldt hills", "bird", "#62f0a0", "Valley edge", "Illustrative songbird overlay on the Flemish Ardennes. Wooded banks and orchards link the hills."],
  [[4.15, 50.72], 13, 9, 0.35, "Eurasian beaver", "Dender woods", "beaver", "#ffd46a", "Brook woodland", "Demo beaver habitat along the Dender. Woody debris in side streams gives them a foothold."],
  [[4.42, 50.78], 12, 8, 0.55, "Riparian songbirds", "Sonian Forest", "bird", "#6aff98", "Urban forest", "Illustrative songbird and bat habitat on the edge of Brussels. Quiet cores inside the beech keep the overlay."],
  [[4.05, 50.55], 13, 9, 0.15, "Natterjack toad", "Hainaut ponds", "toad", "#ffb26a", "Pond mosaic", "Demo toad and newt habitat on Hainaut ponds. Unshaded scrapes after mining keep warm water."],
  [[4.55, 50.28], 14, 10, -0.4, "European eel", "Meuse–Sambre fork", "eel", "#4dffb0", "River fork", "Illustrative eel habitat at the Sambre–Meuse join. Fish-friendly weirs reopen the run."],
  [[5.15, 50.55], 14, 10, 0.25, "Northern pike", "Hesbaye ponds", "fish", "#62e8d0", "Plateau ponds", "Demo pike and heron habitat on the Hesbaye plateau. Restored dew ponds hold a breeding patch."],
  [[5.35, 50.42], 13, 9, 0.7, "Eurasian beaver", "Condroz streams", "beaver", "#ffdc7a", "Limestone brooks", "Illustrative beaver overlay in the Condroz. Connected woody banks let them move between valleys."],
  [[5.05, 49.95], 15, 11, 0.2, "Black grouse", "Famenne forests", "bird", "#d4e86a", "Forest mosaic", "Demo grouse and wildcat habitat in the Famenne. Open rides inside the oak keep a lek."],
  [[5.45, 49.78], 14, 10, -0.25, "Riparian songbirds", "Gaume woods", "bird", "#6ee8a4", "Southern wood", "Illustrative songbird habitat in the Gaume. Wet alder along the Ton keeps the corridor."],
  [[5.75, 49.92], 12, 8, 0.5, "European eel", "Semois bends", "eel", "#5affb8", "Meander nursery", "Demo eel and kingfisher habitat on the Semois. Leaving woody snags in the bends holds the overlay."],
  [[5.85, 50.35], 13, 9, 0.1, "Natterjack toad", "Spa plateaus", "toad", "#ffc46a", "High fen", "Illustrative toad and grouse habitat near Spa. Blocking a few drains keeps the moss wet."],
  [[6.35, 49.82], 12, 8, 0.4, "Riparian songbirds", "Mullerthal sandstone", "bird", "#7affc0", "Sandstone gorges", "Demo songbird and bat habitat in the Mullerthal. Quiet gorges and wet woodland keep the overlay."],
  [[6.42, 49.62], 11, 7, -0.3, "Northern pike", "Moselle terraces", "fish", "#5ce8d8", "River terraces", "Illustrative pike and frog habitat on the Moselle. Side arms below the vineyards hold spawning."],
  [[5.92, 49.95], 13, 9, 0.65, "Eurasian beaver", "Upper Sûre lake", "beaver", "#ffe08a", "Reservoir woods", "Demo beaver and osprey habitat around the Upper Sûre. Woody shores and a quiet arm keep both species."],
  [[6.08, 50.08], 12, 8, 0.2, "Black grouse", "Éislek ridges", "bird", "#d8e07a", "Ridge heath", "Illustrative grouse overlay on Luxembourg’s northern ridges. Open heath after spruce removal holds a lek."],
  [[4.95, 51.02], 13, 9, 0.3, "Migratory geese", "Demer valley", "bird", "#6affd4", "Valley stopover", "Demo geese and eel habitat along the Demer. Restored flood meadows keep a stopover between Kempen and Scheldt."],
  [[4.65, 50.95], 12, 8, -0.5, "Riparian songbirds", "Dijle woods", "bird", "#58f0a8", "Wooded valley", "Illustrative songbird habitat on the Dijle. Connected woods south of Leuven keep the corridor."],
  [[5.45, 51.05], 13, 9, 0.15, "Eurasian beaver", "Hoge Kempen", "beaver", "#ffd46a", "Heath–pine mosaic", "Demo beaver and nightjar habitat in Hoge Kempen. Wet heath and woody streams hold the overlay."],
  [[3.95, 51.28], 12, 8, 0.8, "Northern pike", "Waasland polders", "fish", "#5cffc0", "Polder creeks", "Illustrative pike habitat in the Waasland. Fish-friendly sluices reconnect the creeks to the Scheldt."],
];

export const animalHabitatCollection = {
  type: "FeatureCollection",
  features: patches.map(([center, kmX, kmY, rotation, species, place, icon, color, status, description]) =>
    habitat(center, kmX, kmY, rotation, { species, place, icon, color, status, description }),
  ),
};

export const animalHabitatPoints = {
  type: "FeatureCollection",
  features: animalHabitatCollection.features.map((feature) => ({
    type: "Feature",
    properties: feature.properties,
    geometry: { type: "Point", coordinates: feature.properties.center },
  })),
};
