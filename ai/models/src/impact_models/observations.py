from __future__ import annotations

import json
import math
from typing import Any

import pandas as pd

from impact_models.context import taxa
from impact_models.geo import haversine_m
from impact_models.paths import PROCESSED_DIR, ensure_data_dirs
from impact_models.warehouse import (
    gbif_points as warehouse_gbif,
    roadkill_points as warehouse_roadkill,
    warehouse_flags,
)

GBIF_POINTS = PROCESSED_DIR / "gbif_points.parquet"
ROADKILL_POINTS = PROCESSED_DIR / "roadkill_points.parquet"
FETCH_STATUS = PROCESSED_DIR / "fetch_status.json"

ALLOWED_LICENSES = {"cc0", "cc by", "cc-by", "cc_by", "ccby"}


def _empty_points() -> pd.DataFrame:
    return pd.DataFrame(columns=["lng", "lat", "taxon_id", "scientificName"])


def _parquet(path) -> pd.DataFrame:
    ensure_data_dirs()
    if not path.exists():
        return _empty_points()
    frame = pd.read_parquet(path)
    if frame.empty:
        return _empty_points()
    return frame


def load_gbif_points() -> pd.DataFrame:
    warehouse = warehouse_gbif()
    if not warehouse.empty:
        return warehouse
    return _parquet(GBIF_POINTS)


def load_roadkill_points() -> pd.DataFrame:
    warehouse = warehouse_roadkill()
    if not warehouse.empty:
        return warehouse
    return _parquet(ROADKILL_POINTS)


def load_fetch_status() -> dict[str, Any]:
    flags = warehouse_flags()
    ensure_data_dirs()
    extra: dict[str, Any] = {}
    if FETCH_STATUS.exists():
        extra = json.loads(FETCH_STATUS.read_text(encoding="utf-8"))
    merged = {**extra, **flags}
    merged["gbif"] = bool(flags.get("gbif") or extra.get("gbif"))
    merged["roadkill"] = bool(flags.get("roadkill") or extra.get("roadkill"))
    return merged


def save_fetch_status(status: dict[str, Any]) -> None:
    ensure_data_dirs()
    FETCH_STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")


def save_points(path, rows: list[dict[str, Any]]) -> None:
    ensure_data_dirs()
    frame = pd.DataFrame(rows) if rows else _empty_points()
    frame.to_parquet(path, index=False)


def kernel_intensity(center: tuple[float, float], points: pd.DataFrame, radius_m: float) -> float:
    if points.empty:
        return 0.0
    total = 0.0
    scale = radius_m if radius_m > 0 else 1.0
    for row in points.itertuples(index=False):
        dist = haversine_m(center, (float(row.lng), float(row.lat)))
        if dist > radius_m * 3:
            continue
        total += math.exp(-(dist ** 2) / (2 * scale ** 2))
    return float(total)


def count_within(center: tuple[float, float], points: pd.DataFrame, radius_m: float) -> int:
    if points.empty:
        return 0
    n = 0
    for row in points.itertuples(index=False):
        if haversine_m(center, (float(row.lng), float(row.lat))) <= radius_m:
            n += 1
    return n


def gbif_features(center: tuple[float, float]) -> dict[str, float]:
    points = load_gbif_points()
    out: dict[str, float] = {}
    overall = 0.0
    for taxon in taxa():
        subset = points[points["taxon_id"] == taxon["id"]] if not points.empty else points
        value = kernel_intensity(center, subset, 500)
        out[f"gbif_{taxon['id']}"] = value
        overall += value
    out["gbif_count_500m"] = float(count_within(center, points, 500))
    out["gbif_count_2km"] = float(count_within(center, points, 2000))
    out["gbif_suitability"] = overall
    return out


def roadkill_features(center: tuple[float, float]) -> dict[str, float]:
    points = load_roadkill_points()
    return {
        "roadkill_intensity_2km": kernel_intensity(center, points, 2000),
        "roadkill_count_2km": float(count_within(center, points, 2000)),
    }


def license_ok(value: str | None) -> bool:
    if not value:
        return False
    text = value.lower().replace("_", " ").replace("-", " ")
    compact = text.replace(" ", "")
    return compact in {"cc0", "ccby", "ccby4.0", "ccby3.0"} or "cc0" in compact or compact.startswith("ccby")
