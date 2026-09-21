from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from impact_models.geo import in_bbox
from impact_models.paths import CONTEXT_PATH


@lru_cache(maxsize=1)
def load_context() -> dict[str, Any]:
    with CONTEXT_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def project_type(type_id: str) -> dict[str, Any]:
    for item in load_context()["projectTypes"]:
        if item["id"] == type_id:
            return item
    raise KeyError(f"Unknown typeId: {type_id}")


def habitats() -> list[dict[str, Any]]:
    return load_context()["habitats"]


def water_bodies() -> list[dict[str, Any]]:
    return load_context()["waterBodies"]


def bbox() -> list[float]:
    return list(load_context()["bbox"])


def taxa() -> list[dict[str, Any]]:
    return load_context()["taxa"]


def countries() -> list[dict[str, Any]]:
    return load_context().get("countries") or []


def _bbox_area(bbox: list[float]) -> float:
    west, south, east, north = bbox
    return max(0.0, east - west) * max(0.0, north - south)


def _bbox_distance(lng: float, lat: float, bbox: list[float]) -> float:
    west, south, east, north = bbox
    if in_bbox(lng, lat, bbox):
        return 0.0
    dx = 0.0 if west <= lng <= east else min(abs(lng - west), abs(lng - east))
    dy = 0.0 if south <= lat <= north else min(abs(lat - south), abs(lat - north))
    return (dx * dx + dy * dy) ** 0.5


def country_for_point(center: tuple[float, float]) -> str:
    lng, lat = center
    boxes = countries()
    matching = [item for item in boxes if in_bbox(lng, lat, item["bbox"])]
    if matching:
        matching.sort(key=lambda item: _bbox_area(item["bbox"]))
        return str(matching[0]["id"])
    if not boxes:
        return "NL"
    nearest = min(boxes, key=lambda item: _bbox_distance(lng, lat, item["bbox"]))
    return str(nearest["id"])


def country_index(center: tuple[float, float]) -> int:
    order = {"NL": 0, "BE": 1, "LU": 2}
    return order.get(country_for_point(center), 0)
