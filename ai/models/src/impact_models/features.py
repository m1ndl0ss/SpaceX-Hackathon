from __future__ import annotations

import math

from impact_models.context import habitats, project_type, taxa, water_bodies
from impact_models.geo import clamp, haversine_m, polygon_centroid, radius_hits_polygon
from impact_models.observations import gbif_features, load_fetch_status, roadkill_features
from impact_models.schema import Site, Treatment

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
        "lng",
        "lat",
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
    ]
    + [f"dist_{item['id']}_m" for item in habitats()]
    + [f"dist_water_{item['id']}_m" for item in water_bodies()]
    + [f"gbif_{item['id']}" for item in taxa()]
    + ["gbif_count_500m", "gbif_count_2km", "gbif_suitability", "roadkill_intensity_2km", "roadkill_count_2km"]
)


def outer_radius_m(type_id: str) -> float:
    rings = project_type(type_id)["rings"]
    return float(rings[-1]["radiusM"])


def hit_sites(center: tuple[float, float], type_id: str) -> list[Site]:
    outer = outer_radius_m(type_id)
    sites: list[Site] = []
    for habitat in habitats():
        distance = round(haversine_m(center, tuple(habitat["center"])))
        if distance <= outer + habitat["bufferM"]:
            sites.append(
                Site(
                    id=habitat["id"],
                    name=habitat["name"],
                    kind="habitat",
                    distanceM=distance,
                    species=list(habitat["species"]),
                )
            )
    for body in water_bodies():
        if radius_hits_polygon(center, outer, body["geometry"]):
            centroid = polygon_centroid(body["geometry"])
            sites.append(
                Site(
                    id=body["id"],
                    name=body["name"],
                    kind="water",
                    distanceM=round(haversine_m(center, centroid)),
                    species=[],
                )
            )
    return sites


def feature_row(treatment: Treatment, include_observations: bool = True) -> dict[str, float]:
    center = treatment.center
    spec = project_type(treatment.typeId)
    outer = outer_radius_m(treatment.typeId)
    row: dict[str, float] = {
        "type_idx": float(TYPE_INDEX[treatment.typeId]),
        "lng": center[0],
        "lat": center[1],
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
    for habitat in habitats():
        dist = haversine_m(center, tuple(habitat["center"]))
        habitat_dists.append(dist)
        row[f"dist_{habitat['id']}_m"] = dist
        if dist <= outer + habitat["bufferM"]:
            hits += 1
            proximity += math_exp_decay(dist, habitat["bufferM"])
    row["min_habitat_m"] = min(habitat_dists) if habitat_dists else 9999.0
    row["habitat_hits"] = float(hits)
    row["habitat_proximity"] = proximity

    water_hits = 0
    water_dists: list[float] = []
    for body in water_bodies():
        centroid = polygon_centroid(body["geometry"])
        dist = haversine_m(center, centroid)
        water_dists.append(dist)
        row[f"dist_water_{body['id']}_m"] = dist
        if radius_hits_polygon(center, outer, body["geometry"]):
            water_hits += 1
    row["water_hits"] = float(water_hits)
    row["water_overlap"] = 1.0 if water_hits else 0.0
    row["min_water_m"] = min(water_dists) if water_dists else 9999.0

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


def math_exp_decay(distance_m: float, buffer_m: float) -> float:
    scale = max(buffer_m, 1.0)
    return math.exp(-distance_m / scale)


def data_flags() -> dict[str, bool]:
    status = load_fetch_status()
    return {"gbif": bool(status.get("gbif")), "roadkill": bool(status.get("roadkill"))}


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
