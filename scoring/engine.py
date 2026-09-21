"""Cell-level persistence / risk score for the Abruzzo demo grid.

Higher composite = safer / more suitable bear presence cell.
Deterministic. No LLM in the score.
"""
import json
from datetime import date, datetime, timezone
from math import inf
from pathlib import Path

CELL = 0.05  # ~5 km
WEST, SOUTH, EAST, NORTH = 13.0, 41.4, 14.5, 42.8
RAW = Path(__file__).parent.parent / 'data' / 'raw'
OUT = Path(__file__).parent.parent / 'data' / 'scores'
CACHE = Path(__file__).parent.parent / 'data' / 'cache'

WEIGHTS = {
    'occupancy': 0.35,
    'protection': 0.30,
    'road_safety': 0.20,
    'season': 0.15,
}


def _load(name):
    p = RAW / f'{name}_latest.json'
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding='utf-8'))


def _cell_id(lon, lat):
    cx = WEST + int((lon - WEST) / CELL) * CELL
    cy = SOUTH + int((lat - SOUTH) / CELL) * CELL
    return round(cx, 4), round(cy, 4)


def _in_box(lon, lat, bbox):
    minx, miny, maxx, maxy = bbox
    return minx <= lon <= maxx and miny <= lat <= maxy


def _dist_pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2) ** 0.5


def _min_road_km(lon, lat, roads):
    best = inf
    for r in roads:
        coords = (r.get('geometry') or {}).get('coordinates') or []
        for a, b in zip(coords, coords[1:]):
            d_deg = _dist_pt_seg(lon, lat, a[0], a[1], b[0], b[1])
            best = min(best, d_deg * 111.0)
    return None if best is inf else best


def score_all():
    occs = _load('gbif')
    parks = _load('protected_areas')
    roads = _load('osm_roads')
    weather = _load('open_meteo')

    buckets = {}
    for rec in occs:
        g = rec.get('geometry') or {}
        coords = g.get('coordinates') or []
        if len(coords) < 2:
            continue
        lon, lat = coords
        if not (WEST <= lon <= EAST and SOUTH <= lat <= NORTH):
            continue
        cid = _cell_id(lon, lat)
        b = buckets.setdefault(cid, {'count': 0, 'years': set()})
        b['count'] += 1
        y = rec.get('raw', {}).get('year')
        if y:
            b['years'].add(y)

    snow = 0.0
    precip = 0.0
    n_days = 0
    for w in weather:
        daily = (w.get('raw') or {}).get('daily') or {}
        snows = daily.get('snowfall_sum') or []
        rains = daily.get('precipitation_sum') or []
        for s, r in zip(snows, rains):
            snow += s or 0
            precip += r or 0
            n_days += 1
    snow_avg = snow / n_days if n_days else 0
    # mild winter / low snow is easier movement in this simple demo
    season_score = max(0.0, min(100.0, 80.0 - snow_avg * 8.0 - (precip / max(n_days, 1)) * 0.5))

    cells = []
    for (x, y), b in buckets.items():
        cx, cy = x + CELL / 2, y + CELL / 2
        occupancy = min(100.0, 20.0 + b['count'] * 8.0 + min(20.0, len(b['years']) * 4.0))

        protection = 25.0
        park_name = None
        for p in parks:
            bbox = (p.get('raw') or {}).get('bbox')
            if bbox and _in_box(cx, cy, bbox):
                protection = 90.0 if (p.get('raw') or {}).get('kind') == 'national_park' else 75.0
                park_name = (p.get('raw') or {}).get('name')
                break

        d = _min_road_km(cx, cy, roads)
        if d is None:
            road_safety, road_gap = 50.0, True
        elif d < 0.3:
            road_safety, road_gap = 20.0, False
        elif d < 1.5:
            road_safety, road_gap = 45.0, False
        elif d < 5:
            road_safety, road_gap = 70.0, False
        else:
            road_safety, road_gap = 90.0, False

        composite = (
            occupancy * WEIGHTS['occupancy']
            + protection * WEIGHTS['protection']
            + road_safety * WEIGHTS['road_safety']
            + season_score * WEIGHTS['season']
        )
        cells.append({
            'cell_id': f'{x}_{y}',
            'bbox': [x, y, round(x + CELL, 4), round(y + CELL, 4)],
            'centroid': [round(cx, 4), round(cy, 4)],
            'composite': round(composite, 2),
            'sub_scores': {
                'occupancy': round(occupancy, 2),
                'protection': round(protection, 2),
                'road_safety': round(road_safety, 2),
                'season': round(season_score, 2),
            },
            'signals': {
                'occurrence_count': b['count'],
                'year_span': sorted(b['years']),
                'protected_area': park_name,
                'road_distance_km': None if d is None else round(d, 2),
                'road_data_gap': road_gap,
            },
        })

    cells.sort(key=lambda c: c['composite'], reverse=True)
    result = {
        'species': 'Ursus arctos',
        'region': 'Abruzzo / central Apennines',
        'weights': WEIGHTS,
        'computed_at': datetime.now(timezone.utc).isoformat(),
        'cell_count': len(cells),
        'cells': cells,
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    (OUT / 'cells_latest.json').write_text(payload, encoding='utf-8')
    (OUT / f'cells_{today}.json').write_text(payload, encoding='utf-8')

    bundle = {
        'computed_at': result['computed_at'],
        'scores': result,
        'occurrences': occs,
        'protected_areas': parks,
        'roads': roads,
        'weather': weather,
        'news': _load('news'),
    }
    bundle_text = json.dumps(bundle, ensure_ascii=False, indent=2)
    (CACHE / 'frontend_latest.json').write_text(bundle_text, encoding='utf-8')
    (CACHE / f'frontend_{today}.json').write_text(bundle_text, encoding='utf-8')
    return result
