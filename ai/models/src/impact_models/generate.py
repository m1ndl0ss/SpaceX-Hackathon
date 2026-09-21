from __future__ import annotations

import argparse
import math

import numpy as np
import pandas as pd

from impact_models.context import countries, country_for_point, load_context, taxa
from impact_models.features import FEATURE_COLUMNS, feature_row
from impact_models.geo import clamp
from impact_models.outputs import HEADS, clamp_head_value
from impact_models.schema import NearbyTreatment, Treatment

TYPE_IDS = [item["id"] for item in load_context()["projectTypes"]]
COUNTRY_WEIGHTS = {"NL": 0.45, "BE": 0.40, "LU": 0.15}
HORIZON_YEARS = list(range(2026, 2041))
MASK_RATE = 0.12


def recipe_labels(row: dict[str, float]) -> dict[str, float]:
    wildlife = float(row["_wildlife_prior"])
    land = float(row["_land_prior"])
    water = float(row["_water_prior"])
    energy = float(row["_energy_prior"])
    jobs = float(row["_jobs_prior"])
    carbon = float(row["_carbon_prior"])
    scale = max(0.4, float(row["scale"]))

    wildlife -= 1.4 * float(row["habitat_proximity"])
    if row["min_habitat_m"] < 400:
        wildlife -= 0.8
    if row["water_overlap"] and row["_water_bump"]:
        water = clamp(water + row["_water_bump"])
    if row["cooling"]:
        water = clamp(water + 2)
    if row["buffer"]:
        wildlife = clamp(wildlife + 2)
        land = clamp(land + 1)
        water = clamp(water + 1)

    suitability = 1.0 + 0.15 * float(row["gbif_suitability"])
    habitat = max(0.0, -wildlife * 12.0 * scale) * suitability
    if int(row["type_idx"]) == 3:
        habitat *= 1.0 + 0.25 * float(row["roadkill_intensity_2km"])
        if row["min_road_km"] < 1.5 and float(row.get("has_osm_roads") or 0) > 0:
            habitat *= 1.15
    elif int(row["type_idx"]) == 2:
        habitat *= 1.0 + 0.08 * float(row["roadkill_intensity_2km"])

    nearby_500 = float(row.get("nearby_500m") or 0.0)
    nearby_2km = float(row.get("nearby_2km") or 0.0)
    nearby_highway = float(row.get("nearby_highway_2km") or 0.0)
    extra_2km = max(0.0, nearby_2km - nearby_500)
    habitat += 1.8 * nearby_500 + 0.7 * extra_2km
    habitat *= 1.0 + 0.15 * nearby_highway

    river = max(0.0, -water * 0.45 * (1.15 if row["water_overlap"] else 1.0))
    river += 0.08 * nearby_2km
    stress = max(0.0, -land * 4.0 * scale)
    if energy < 0:
        energy_idx = -energy * 1.35 * scale
    else:
        energy_idx = max(0.0, 1.2 - energy * 0.15)
    energy_idx += 0.12 * nearby_2km

    if float(row.get("has_open_meteo") or 0.0) > 0:
        precip = float(row.get("precip_mm") or 0.0)
        snow = float(row.get("snow_mm") or 0.0)
        stress *= 1.0 / (1.0 + 0.008 * precip + 0.02 * snow)
        river *= 1.0 / (1.0 + 0.004 * precip)

    years = float(row["horizon_year"]) - 2026.0
    construction = max(0.0, 1.0 - years / 9.0)
    ops = max(0.35, jobs * 0.45)
    jobs_fte = (jobs * 8.0 * construction + ops * 6.0) * scale

    tco2e = -carbon * 120.0 * scale
    if energy < 0:
        tco2e += -energy * 80.0 * scale
    if tco2e > 0:
        tco2e *= 1.0 + 0.04 * years
    else:
        tco2e *= 1.0 + 0.02 * years

    labels = {
        "habitatHa": habitat,
        "riverTempC": river,
        "vegStress": stress,
        "energyIdx": energy_idx,
        "jobsFte": max(0.0, jobs_fte),
        "tco2e": tco2e,
    }
    return {key: clamp_head_value(key, float(value)) for key, value in labels.items()}


def physical_labels(row: dict[str, float], rng: np.random.Generator) -> dict[str, float]:
    labels = recipe_labels(row)
    for key, value in labels.items():
        noise = rng.normal(0.0, 0.08 * abs(value) + 0.04)
        labels[key] = clamp_head_value(key, float(value + noise))
    return labels


def _sample_center(rng: np.random.Generator) -> tuple[float, float]:
    boxes = countries()
    ids = [item["id"] for item in boxes]
    weights = np.array([COUNTRY_WEIGHTS.get(item_id, 0.1) for item_id in ids], dtype=float)
    weights = weights / weights.sum()
    choice = int(rng.choice(len(boxes), p=weights))
    intended = str(boxes[choice]["id"])
    west, south, east, north = boxes[choice]["bbox"]
    cx, cy = (west + east) / 2.0, (south + north) / 2.0
    for attempt in range(40):
        if attempt < 28:
            lng = float(rng.uniform(west, east))
            lat = float(rng.uniform(south, north))
        else:
            span = 0.25
            lng = float(rng.uniform(cx - span * (east - west) / 2.0, cx + span * (east - west) / 2.0))
            lat = float(rng.uniform(cy - span * (north - south) / 2.0, cy + span * (north - south) / 2.0))
        if country_for_point((lng, lat)) == intended:
            return lng, lat
    return float(cx), float(cy)


def _offset_center(center: tuple[float, float], dist_m: float, bearing: float) -> tuple[float, float]:
    lng, lat = center
    dlat = (dist_m * math.cos(bearing)) / 110540.0
    dlng = (dist_m * math.sin(bearing)) / (111320.0 * max(0.15, math.cos(math.radians(lat))))
    return float(lng + dlng), float(lat + dlat)


def _sample_nearby(center: tuple[float, float], rng: np.random.Generator) -> list[NearbyTreatment]:
    if rng.random() >= 0.5:
        return []
    count = int(rng.integers(1, 4))
    nearby: list[NearbyTreatment] = []
    for _ in range(count):
        dist_m = float(rng.uniform(80.0, 2000.0))
        bearing = float(rng.uniform(0.0, 2.0 * math.pi))
        type_id = "highway" if rng.random() < 0.25 else str(rng.choice(TYPE_IDS))
        nearby.append(NearbyTreatment(typeId=type_id, center=_offset_center(center, dist_m, bearing)))
    return nearby


def _mask_sources(row: dict[str, float], rng: np.random.Generator) -> dict[str, float]:
    if float(row.get("has_gbif") or 0) > 0 and rng.random() < MASK_RATE:
        for taxon in taxa():
            row[f"gbif_{taxon['id']}"] = 0.0
        row["gbif_count_500m"] = 0.0
        row["gbif_count_2km"] = 0.0
        row["gbif_suitability"] = 0.0
        row["has_gbif"] = 0.0
    if float(row.get("has_roadkill") or 0) > 0 and rng.random() < MASK_RATE:
        row["roadkill_intensity_2km"] = 0.0
        row["roadkill_count_2km"] = 0.0
        row["has_roadkill"] = 0.0
    if float(row.get("has_osm_roads") or 0) > 0 and rng.random() < MASK_RATE:
        row["min_road_km"] = 25.0
        row["has_osm_roads"] = 0.0
    if float(row.get("has_open_meteo") or 0) > 0 and rng.random() < MASK_RATE:
        row["snow_mm"] = 0.0
        row["precip_mm"] = 0.0
        row["has_open_meteo"] = 0.0
    return row


def generate_frame(n: int = 6000, seed: int = 7, include_observations: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, float]] = []
    for _ in range(n):
        center = _sample_center(rng)
        treatment = Treatment(
            typeId=str(rng.choice(TYPE_IDS)),
            center=center,
            horizonYear=int(rng.choice(HORIZON_YEARS)),
            cooling=bool(rng.random() < 0.3),
            buffer=bool(rng.random() < 0.3),
            scale=float(np.clip(rng.normal(1.0, 0.28), 0.4, 2.0)),
            nearbyTreatments=_sample_nearby(center, rng),
        )
        row = feature_row(treatment, include_observations=include_observations)
        if include_observations:
            row = _mask_sources(row, rng)
        labels = physical_labels(row, rng)
        packed = {name: row[name] for name in FEATURE_COLUMNS}
        packed.update(labels)
        rows.append(packed)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Benelux treatment rows.")
    parser.add_argument("--n", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    frame = generate_frame(n=args.n, seed=args.seed)
    if args.out:
        frame.to_parquet(args.out, index=False)
        print(f"wrote {len(frame)} rows to {args.out}")
    else:
        print(frame[list(HEADS)].describe().to_string())


if __name__ == "__main__":
    main()
