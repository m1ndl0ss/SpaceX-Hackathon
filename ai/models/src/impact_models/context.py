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


def country_for_point(center: tuple[float, float]) -> str:
    lng, lat = center
    for item in countries():
        if in_bbox(lng, lat, item["bbox"]):
            return item["id"]
    return "NL"


def country_index(center: tuple[float, float]) -> int:
    order = {"NL": 0, "BE": 1, "LU": 2}
    return order.get(country_for_point(center), 0)
