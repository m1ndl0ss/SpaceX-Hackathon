from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import pandas as pd

from impact_models.context import bbox, load_context, taxa
from impact_models.geo import geometry_centroid, in_bbox
from impact_models import paths


def warehouse_file(name: str) -> Any:
    directory = paths.WAREHOUSE_DIR
    path = directory / f"{name}_latest.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def _clip_point(lng: float, lat: float) -> bool:
    return in_bbox(lng, lat, bbox())


def _license_ok(value: str | None) -> bool:
    if not value:
        return False
    compact = value.lower().replace("_", "").replace("-", "").replace(" ", "")
    return compact.startswith("cc0") or compact.startswith("ccby")


def _record_point(record: dict[str, Any]) -> tuple[float, float] | None:
    geom = record.get("geometry") or {}
    coords = geom.get("coordinates")
    kind = geom.get("type")
    if kind == "Point" and isinstance(coords, list) and len(coords) >= 2:
        return float(coords[0]), float(coords[1])
    raw = record.get("raw") or {}
    lng = raw.get("decimalLongitude")
    lat = raw.get("decimalLatitude")
    if lng is not None and lat is not None:
        return float(lng), float(lat)
    return None


def _taxon_id(scientific: str) -> str | None:
    text = (scientific or "").lower()
    for taxon in taxa():
        name = taxon["scientificName"].lower()
        if text.startswith(name) or name in text:
            return taxon["id"]
    return None


def _empty_points() -> pd.DataFrame:
    return pd.DataFrame(columns=["lng", "lat", "taxon_id", "scientificName"])


@lru_cache(maxsize=1)
def gbif_points() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for record in warehouse_file("gbif"):
        point = _record_point(record)
        if point is None or not _clip_point(*point):
            continue
        if not _license_ok(str(record.get("license") or "")):
            continue
        scientific = str((record.get("raw") or {}).get("scientificName") or "")
        taxon_id = _taxon_id(scientific)
        if taxon_id is None:
            continue
        rows.append({"lng": point[0], "lat": point[1], "taxon_id": taxon_id, "scientificName": scientific})
    return pd.DataFrame(rows) if rows else _empty_points()


@lru_cache(maxsize=1)
def roadkill_points() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    names = [item["scientificName"].lower() for item in load_context().get("roadkillGroups", [])]
    for record in warehouse_file("roadkill"):
        point = _record_point(record)
        if point is None or not _clip_point(*point):
            continue
        raw = record.get("raw") or {}
        scientific = str(raw.get("scientificName") or raw.get("species") or "")
        stem = scientific.lower()
        if names and not any(name in stem for name in names):
            continue
        taxon_id = stem.replace(" ", "_") if stem else "unknown"
        rows.append({"lng": point[0], "lat": point[1], "taxon_id": taxon_id, "scientificName": scientific})
    return pd.DataFrame(rows) if rows else _empty_points()


def _named_geometry(record: dict[str, Any], default_kind: str) -> dict[str, Any] | None:
    geom = record.get("geometry")
    if not geom or not geom.get("type"):
        raw = record.get("raw") or {}
        box = raw.get("bbox")
        if isinstance(box, list) and len(box) == 4:
            from impact_models.geo import box_polygon

            geom = box_polygon(box[0], box[1], box[2], box[3])
        else:
            return None
    centroid = geometry_centroid(geom)
    if not _clip_point(*centroid):
        return None
    raw = record.get("raw") or {}
    ident = str(raw.get("id") or record.get("source_id") or centroid)
    name = str(raw.get("name") or ident)
    return {
        "id": ident,
        "name": name,
        "kind": default_kind,
        "geometry": geom,
        "center": list(centroid),
        "bufferM": int(raw.get("bufferM") or 500),
        "species": list(raw.get("species") or []),
    }


@lru_cache(maxsize=1)
def protected_geometries() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for record in warehouse_file("protected_areas"):
        parsed = _named_geometry(record, "habitat")
        if parsed:
            items.append(parsed)
    return items


@lru_cache(maxsize=1)
def water_geometries() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for record in warehouse_file("water"):
        parsed = _named_geometry(record, "water")
        if parsed:
            items.append(parsed)
    return items


@lru_cache(maxsize=1)
def road_geometries() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for record in warehouse_file("osm_roads"):
        geom = record.get("geometry") or {}
        kind = geom.get("type")
        if kind == "LineString":
            pieces = [geom]
        elif kind == "MultiLineString":
            pieces = [{"type": "LineString", "coordinates": line} for line in (geom.get("coordinates") or [])]
        else:
            continue
        for piece in pieces:
            centroid = geometry_centroid(piece)
            if not _clip_point(*centroid):
                continue
            items.append(piece)
    return items


def _daily_mean(values: list) -> float:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return 0.0
    return sum(nums) / len(nums)


@lru_cache(maxsize=1)
def weather_sites() -> list[dict[str, Any]]:
    sites: list[dict[str, Any]] = []
    for record in warehouse_file("open_meteo"):
        point = _record_point(record)
        if point is None or not _clip_point(*point):
            continue
        daily = (record.get("raw") or {}).get("daily") or {}
        sites.append(
            {
                "center": point,
                "snow_mm": _daily_mean(daily.get("snowfall_sum") or []),
                "precip_mm": _daily_mean(daily.get("precipitation_sum") or []),
                "wind_ms": _daily_mean(daily.get("wind_speed_10m_max") or []),
            }
        )
    return sites


@lru_cache(maxsize=1)
def news_headlines() -> list[str]:
    titles: list[str] = []
    for record in warehouse_file("news"):
        point = _record_point(record)
        if point is not None and not _clip_point(*point):
            continue
        title = str((record.get("raw") or {}).get("title") or "").strip()
        if title:
            titles.append(title)
    return titles[:8]


def warehouse_flags() -> dict[str, bool]:
    return {
        "gbif": not gbif_points().empty,
        "roadkill": not roadkill_points().empty,
        "protected_areas": bool(protected_geometries()),
        "water": bool(water_geometries()),
        "osm_roads": bool(road_geometries()),
        "open_meteo": bool(weather_sites()),
        "news": bool(news_headlines()),
    }


def clear_warehouse_cache() -> None:
    gbif_points.cache_clear()
    roadkill_points.cache_clear()
    protected_geometries.cache_clear()
    water_geometries.cache_clear()
    road_geometries.cache_clear()
    weather_sites.cache_clear()
    news_headlines.cache_clear()
