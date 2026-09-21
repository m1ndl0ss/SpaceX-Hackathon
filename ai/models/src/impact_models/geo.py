from __future__ import annotations

import math
from typing import Any

EARTH_M = 6_371_000


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lng1, lat1 = a
    lng2, lat2 = b
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    sine = math.sin(d_lat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(d_lng / 2) ** 2
    return 2 * EARTH_M * math.asin(min(1.0, math.sqrt(sine)))


def circle_coords(center: tuple[float, float], radius_m: float, steps: int = 48) -> list[tuple[float, float]]:
    lng, lat = center
    lat_rad = math.radians(lat)
    m_per_deg_lat = 110540
    m_per_deg_lng = 111320 * max(0.15, math.cos(lat_rad))
    coords: list[tuple[float, float]] = []
    for i in range(steps + 1):
        angle = (i / steps) * math.pi * 2
        coords.append((lng + math.cos(angle) * radius_m / m_per_deg_lng, lat + math.sin(angle) * radius_m / m_per_deg_lat))
    return coords


def point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    j = len(ring) - 1
    for i, vertex in enumerate(ring):
        xi, yi = vertex
        xj, yj = ring[j]
        intersect = (yi > y) != (yj > y) and x < ((xj - xi) * (y - yi)) / ((yj - yi) or 1e-12) + xi
        if intersect:
            inside = not inside
        j = i
    return inside


def point_in_polygon(point: tuple[float, float], polygon: dict[str, Any]) -> bool:
    ring = polygon["coordinates"][0]
    return point_in_ring(point, ring)


def radius_hits_polygon(center: tuple[float, float], radius_m: float, polygon: dict[str, Any]) -> bool:
    if point_in_polygon(center, polygon):
        return True
    ring = polygon["coordinates"][0]
    for coord in ring:
        if haversine_m(center, (coord[0], coord[1])) <= radius_m:
            return True
    return any(point_in_polygon(pt, polygon) for pt in circle_coords(center, radius_m, 48))


def polygon_centroid(polygon: dict[str, Any]) -> tuple[float, float]:
    ring = polygon["coordinates"][0][:-1] or polygon["coordinates"][0]
    lng = sum(p[0] for p in ring) / len(ring)
    lat = sum(p[1] for p in ring) / len(ring)
    return (lng, lat)


def clamp(value: float, lo: float = -5.0, hi: float = 5.0) -> float:
    return max(lo, min(hi, value))
