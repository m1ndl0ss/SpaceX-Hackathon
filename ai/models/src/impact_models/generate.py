from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from impact_models.context import bbox, load_context
from impact_models.features import FEATURE_COLUMNS, feature_row, vectorize
from impact_models.geo import clamp
from impact_models.schema import Treatment

HEADS = ("habitatHa", "riverTempC", "vegStress", "energyIdx", "jobsFte", "tco2e")
TYPE_IDS = [item["id"] for item in load_context()["projectTypes"]]


def physical_labels(row: dict[str, float], rng: np.random.Generator) -> dict[str, float]:
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
    elif int(row["type_idx"]) == 2:
        habitat *= 1.0 + 0.08 * float(row["roadkill_intensity_2km"])

    river = max(0.0, -water * 0.45 * (1.15 if row["water_overlap"] else 1.0))
    stress = max(0.0, -land * 4.0 * scale)
    if energy < 0:
        energy_idx = -energy * 1.35 * scale
    else:
        energy_idx = max(0.0, 1.2 - energy * 0.15)

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
    for key, value in labels.items():
        noise = rng.normal(0.0, 0.08 * abs(value) + 0.04)
        labels[key] = float(value + noise)
    return labels


def generate_frame(n: int = 6000, seed: int = 7, include_observations: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    west, south, east, north = bbox()
    rows: list[dict[str, float]] = []
    for _ in range(n):
        treatment = Treatment(
            typeId=str(rng.choice(TYPE_IDS)),
            center=(float(rng.uniform(west, east)), float(rng.uniform(south, north))),
            horizonYear=int(rng.choice([2026, 2030, 2035])),
            cooling=bool(rng.random() < 0.3),
            buffer=bool(rng.random() < 0.3),
            scale=float(np.clip(rng.normal(1.0, 0.18), 0.5, 1.8)),
        )
        row = feature_row(treatment, include_observations=include_observations)
        labels = physical_labels(row, rng)
        packed = {name: row[name] for name in FEATURE_COLUMNS}
        packed.update(labels)
        rows.append(packed)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Limburg treatment rows.")
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
