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


def box_polygon(west: float, south: float, east: float, north: float) -> dict[str, Any]:
    ring = [[west, south], [east, south], [east, north], [west, north], [west, south]]
    return {"type": "Polygon", "coordinates": [ring]}


def circle_polygon(center: tuple[float, float], radius_m: float, steps: int = 32) -> dict[str, Any]:
    return {"type": "Polygon", "coordinates": [list(circle_coords(center, radius_m, steps))]}


def in_bbox(lng: float, lat: float, bbox: list[float]) -> bool:
    west, south, east, north = bbox
    return west <= lng <= east and south <= lat <= north


def geometry_centroid(geometry: dict[str, Any]) -> tuple[float, float]:
    kind = geometry.get("type")
    if kind == "Point":
        coords = geometry["coordinates"]
        return (float(coords[0]), float(coords[1]))
    if kind == "LineString":
        coords = geometry["coordinates"]
        lng = sum(p[0] for p in coords) / max(len(coords), 1)
        lat = sum(p[1] for p in coords) / max(len(coords), 1)
        return (float(lng), float(lat))
    if kind == "MultiLineString":
        coords = [pt for line in (geometry.get("coordinates") or []) for pt in line]
        lng = sum(p[0] for p in coords) / max(len(coords), 1)
        lat = sum(p[1] for p in coords) / max(len(coords), 1)
        return (float(lng), float(lat))
    if kind == "MultiPolygon":
        return geometry_centroid({"type": "Polygon", "coordinates": geometry["coordinates"][0]})
    return polygon_centroid(geometry)


def min_dist_linestring_m(point: tuple[float, float], coords: list) -> float:
    if not coords:
        return 1e9
    best = haversine_m(point, (float(coords[0][0]), float(coords[0][1])))
    for a, b in zip(coords, coords[1:]):
        best = min(best, _point_segment_m(point, (float(a[0]), float(a[1])), (float(b[0]), float(b[1]))))
    return best


def _point_segment_m(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    lng, lat = p
    mid_lat = math.radians((a[1] + b[1] + lat) / 3)
    mx = 111320 * max(0.15, math.cos(mid_lat))
    my = 110540
    px, py = lng * mx, lat * my
    ax, ay = a[0] * mx, a[1] * my
    bx, by = b[0] * mx, b[1] * my
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2) ** 0.5


def min_dist_geometry_m(point: tuple[float, float], geometry: dict[str, Any]) -> float:
    kind = geometry.get("type")
    if kind == "Point":
        coords = geometry["coordinates"]
        return haversine_m(point, (float(coords[0]), float(coords[1])))
    if kind == "LineString":
        return min_dist_linestring_m(point, geometry.get("coordinates") or [])
    if kind == "MultiLineString":
        parts = geometry.get("coordinates") or []
        if not parts:
            return 1e9
        return min(min_dist_linestring_m(point, line) for line in parts)
    if kind == "Polygon":
        if point_in_polygon(point, geometry):
            return 0.0
        ring = geometry["coordinates"][0]
        return min_dist_linestring_m(point, ring)
    if kind == "MultiPolygon":
        polys = geometry.get("coordinates") or []
        if not polys:
            return 1e9
        return min(min_dist_geometry_m(point, {"type": "Polygon", "coordinates": poly}) for poly in polys)
    return 1e9


def radius_hits_geometry(center: tuple[float, float], radius_m: float, geometry: dict[str, Any]) -> bool:
    kind = geometry.get("type")
    if kind == "Polygon":
        return radius_hits_polygon(center, radius_m, geometry)
    if kind == "MultiPolygon":
        return any(
            radius_hits_polygon(center, radius_m, {"type": "Polygon", "coordinates": poly})
            for poly in (geometry.get("coordinates") or [])
        )
    return min_dist_geometry_m(center, geometry) <= radius_m
