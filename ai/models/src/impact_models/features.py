from __future__ import annotations

import math

from impact_models.context import (
    country_for_point,
    country_index,
    habitats,
    project_type,
    taxa,
    water_bodies,
)
from impact_models.geo import (
    circle_polygon,
    clamp,
    haversine_m,
    min_dist_geometry_m,
    radius_hits_geometry,
)
from impact_models.observations import gbif_features, load_fetch_status, roadkill_features
from impact_models.schema import Site, Treatment
from impact_models.warehouse import (
    news_headlines,
    protected_geometries,
    road_geometries,
    water_geometries,
    weather_sites,
)

TYPE_INDEX = {
    "wind": 0,
    "solar": 1,
    "industrial": 2,
    "highway": 3,
    "housing": 4,
    "dam": 5,
    "powerline": 6,
    "datacentre": 7,
}

FEATURE_COLUMNS = (
    [
        "type_idx",
        "country_idx",
        "horizon_year",
        "cooling",
        "buffer",
        "scale",
        "nearby_500m",
        "nearby_2km",
        "nearby_highway_2km",
        "min_habitat_m",
        "habitat_hits",
        "habitat_proximity",
        "water_hits",
        "water_overlap",
        "min_water_m",
        "min_road_km",
        "snow_mm",
        "precip_mm",
    ]
    + [f"gbif_{item['id']}" for item in taxa()]
    + ["gbif_count_500m", "gbif_count_2km", "gbif_suitability", "roadkill_intensity_2km", "roadkill_count_2km"]
)


def outer_radius_m(type_id: str) -> float:
    rings = project_type(type_id)["rings"]
    return float(rings[-1]["radiusM"])


def _habitat_layers() -> list[dict]:
    warehouse = protected_geometries()
    if warehouse:
        return warehouse
    layers = []
    for habitat in habitats():
        center = tuple(habitat["center"])
        buffer_m = float(habitat.get("bufferM") or 500)
        layers.append(
            {
                **habitat,
                "center": list(center),
                "geometry": circle_polygon(center, buffer_m),
            }
        )
    return layers


def _water_layers() -> list[dict]:
    warehouse = water_geometries()
    if warehouse:
        return warehouse
    return list(water_bodies())


def hit_sites(center: tuple[float, float], type_id: str) -> list[Site]:
    outer = outer_radius_m(type_id)
    sites: list[Site] = []
    for habitat in _habitat_layers():
        geom = habitat.get("geometry") or circle_polygon(tuple(habitat["center"]), float(habitat.get("bufferM") or 500))
        distance = round(min_dist_geometry_m(center, geom))
        buffer_m = float(habitat.get("bufferM") or 500)
        if distance <= outer + buffer_m:
            sites.append(
                Site(
                    id=str(habitat["id"]),
                    name=str(habitat["name"]),
                    kind="habitat",
                    distanceM=distance,
                    species=list(habitat.get("species") or []),
                )
            )
    for body in _water_layers():
        geom = body["geometry"]
        if radius_hits_geometry(center, outer, geom):
            sites.append(
                Site(
                    id=str(body["id"]),
                    name=str(body["name"]),
                    kind="water",
                    distanceM=round(min_dist_geometry_m(center, geom)),
                    species=[],
                )
            )
    return sites


def _weather_row(center: tuple[float, float]) -> dict[str, float]:
    sites = weather_sites()
    if not sites:
        return {"snow_mm": 0.0, "precip_mm": 0.0}
    nearest = min(sites, key=lambda site: haversine_m(center, tuple(site["center"])))
    return {"snow_mm": float(nearest["snow_mm"]), "precip_mm": float(nearest["precip_mm"])}


def _min_road_km(center: tuple[float, float]) -> float:
    roads = road_geometries()
    if not roads:
        return 25.0
    best = min(min_dist_geometry_m(center, geom) for geom in roads)
    return best / 1000.0


def feature_row(treatment: Treatment, include_observations: bool = True) -> dict[str, float]:
    center = treatment.center
    spec = project_type(treatment.typeId)
    outer = outer_radius_m(treatment.typeId)
    row: dict[str, float] = {
        "type_idx": float(TYPE_INDEX[treatment.typeId]),
        "country_idx": float(country_index(center)),
        "horizon_year": float(treatment.horizonYear),
        "cooling": 1.0 if treatment.cooling else 0.0,
        "buffer": 1.0 if treatment.buffer else 0.0,
        "scale": float(treatment.scale),
        "nearby_500m": 0.0,
        "nearby_2km": 0.0,
        "nearby_highway_2km": 0.0,
    }
    for nearby in treatment.nearbyTreatments:
        dist = haversine_m(center, nearby.center)
        if dist <= 500:
            row["nearby_500m"] += 1
        if dist <= 2000:
            row["nearby_2km"] += 1
            if nearby.typeId == "highway":
                row["nearby_highway_2km"] += 1

    habitat_dists: list[float] = []
    proximity = 0.0
    hits = 0
    for habitat in _habitat_layers():
        geom = habitat.get("geometry") or circle_polygon(tuple(habitat["center"]), float(habitat.get("bufferM") or 500))
        dist = min_dist_geometry_m(center, geom)
        habitat_dists.append(dist)
        buffer_m = float(habitat.get("bufferM") or 500)
        if dist <= outer + buffer_m:
            hits += 1
            proximity += math.exp(-dist / max(buffer_m, 1.0))
    row["min_habitat_m"] = min(habitat_dists) if habitat_dists else 9999.0
    row["habitat_hits"] = float(hits)
    row["habitat_proximity"] = proximity

    water_hits = 0
    water_dists: list[float] = []
    for body in _water_layers():
        dist = min_dist_geometry_m(center, body["geometry"])
        water_dists.append(dist)
        if radius_hits_geometry(center, outer, body["geometry"]):
            water_hits += 1
    row["water_hits"] = float(water_hits)
    row["water_overlap"] = 1.0 if water_hits else 0.0
    row["min_water_m"] = min(water_dists) if water_dists else 9999.0
    row["min_road_km"] = _min_road_km(center)
    row.update(_weather_row(center))

    if include_observations:
        row.update(gbif_features(center))
        row.update(roadkill_features(center))
    else:
        for taxon in taxa():
            row[f"gbif_{taxon['id']}"] = 0.0
        row["gbif_count_500m"] = 0.0
        row["gbif_count_2km"] = 0.0
        row["gbif_suitability"] = 0.0
        row["roadkill_intensity_2km"] = 0.0
        row["roadkill_count_2km"] = 0.0

    row["_water_bump"] = float(spec["waterBump"])
    row["_wildlife_prior"] = float(spec["sectors"]["wildlife"])
    row["_land_prior"] = float(spec["sectors"]["landPollution"])
    row["_water_prior"] = float(spec["sectors"]["waterPollution"])
    row["_energy_prior"] = float(spec["sectors"]["energy"])
    row["_jobs_prior"] = float(spec["sectors"]["jobs"])
    row["_carbon_prior"] = float(spec["sectors"]["carbon"])
    row["_society_prior"] = float(spec["sectors"]["society"])
    row["_noise_prior"] = float(spec["sectors"]["noise"])
    return row


def vectorize(row: dict[str, float]) -> list[float]:
    return [float(row[name]) for name in FEATURE_COLUMNS]


def data_flags() -> dict[str, bool]:
    status = load_fetch_status()
    return {
        "gbif": bool(status.get("gbif")),
        "roadkill": bool(status.get("roadkill")),
        "protected_areas": bool(status.get("protected_areas")),
        "water": bool(status.get("water")),
        "osm_roads": bool(status.get("osm_roads")),
        "open_meteo": bool(status.get("open_meteo")),
        "news": bool(status.get("news")),
    }


def nearby_headlines() -> list[str]:
    return news_headlines()


def lookup_sectors(treatment: Treatment) -> dict[str, float]:
    spec = project_type(treatment.typeId)
    scores = dict(spec["sectors"])
    if treatment.cooling:
        scores["waterPollution"] = clamp(scores["waterPollution"] + 2)
    if treatment.buffer:
        scores["wildlife"] = clamp(scores["wildlife"] + 2)
        scores["landPollution"] = clamp(scores["landPollution"] + 1)
        scores["waterPollution"] = clamp(scores["waterPollution"] + 1)
    return scores


def country_code(center: tuple[float, float]) -> str:
    return country_for_point(center)
