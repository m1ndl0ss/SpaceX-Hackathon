"""Named major rivers and lakes in the Benelux bbox (OSM Overpass)."""
import logging

from collectors.base import CollectedRecord, now_iso
from collectors import overpass
from collectors.region import OVERPASS_BBOX

logger = logging.getLogger(__name__)

SOURCE_ID = 'C007'
LAKE_QL = f"""
[out:json][timeout:25];
(
  nwr["name"="IJsselmeer"]({OVERPASS_BBOX});
  nwr["name"="Markermeer"]({OVERPASS_BBOX});
);
out tags bb 8;
"""
RIVER_QLS = [
    '[out:json][timeout:20];way["waterway"="river"]["name"="Maas"](50.75,5.55,51.05,5.85);out geom 8;',
    '[out:json][timeout:20];way["waterway"="river"]["name"="Meuse"](50.40,4.85,50.70,5.20);out geom 8;',
    '[out:json][timeout:20];way["waterway"="river"]["name"="Schelde"](51.10,4.15,51.30,4.50);out geom 8;',
    '[out:json][timeout:20];way["waterway"="river"]["name"="Waal"](51.80,5.20,51.90,5.90);out geom 8;',
    '[out:json][timeout:20];way["waterway"="river"]["name"="Jeker"](50.80,5.65,50.90,5.73);out geom 6;',
    '[out:json][timeout:20];way["waterway"="river"]["name"="Sûre"](49.70,5.80,49.92,6.15);out geom 6;',
    '[out:json][timeout:20];way["waterway"="river"]["name"="Sauer"](49.70,5.80,49.92,6.15);out geom 6;',
]


def _box_poly(b):
    minx, miny, maxx, maxy = b
    return {'type': 'Polygon', 'coordinates': [[
        [minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]
    ]]}


def _fixtures():
    return [
        CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM water (fixture)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='fixture',
            geometry={'type': 'LineString', 'coordinates': [
                [5.69, 50.85], [5.70, 51.17], [5.48, 51.70], [4.95, 51.82]
            ]},
            raw={'name': 'Maas / Meuse', 'kind': 'river'},
        ),
        CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM water (fixture)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='fixture',
            geometry={'type': 'LineString', 'coordinates': [
                [3.55, 51.05], [4.23, 51.22], [4.40, 51.35]
            ]},
            raw={'name': 'Scheldt / Schelde', 'kind': 'river'},
        ),
        CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM water (fixture)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='fixture',
            geometry={'type': 'LineString', 'coordinates': [
                [6.05, 51.84], [5.85, 51.85], [5.35, 51.83]
            ]},
            raw={'name': 'Rhine / Waal', 'kind': 'river'},
        ),
        CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM water (fixture)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='fixture',
            geometry=_box_poly([5.00, 52.50, 5.70, 53.00]),
            raw={'name': 'IJsselmeer', 'kind': 'lake', 'bbox': [5.00, 52.50, 5.70, 53.00]},
        ),
        CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM water (fixture)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='fixture',
            geometry={'type': 'LineString', 'coordinates': [
                [5.69, 50.82], [5.68, 50.85]
            ]},
            raw={'name': 'Jeker', 'kind': 'river'},
        ),
        CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM water (fixture)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='fixture',
            geometry={'type': 'LineString', 'coordinates': [
                [5.85, 49.85], [6.03, 49.86], [6.10, 49.72]
            ]},
            raw={'name': 'Sûre / Sauer', 'kind': 'river'},
        ),
    ]


def _line_from_el(el):
    geom = el.get('geometry') or []
    if len(geom) < 2:
        return None
    return {'type': 'LineString', 'coordinates': [[p['lon'], p['lat']] for p in geom]}


def _poly_from_bounds(el):
    b = el.get('bounds')
    if not b:
        return None, None
    bbox = [b['minlon'], b['minlat'], b['maxlon'], b['maxlat']]
    return _box_poly(bbox), bbox


def collect_all():
    records = []
    elements = []
    for ql in [LAKE_QL, *RIVER_QLS]:
        try:
            data = overpass.query(ql)
            got = data.get('elements') or []
            logger.info('Overpass water query returned %s elements', len(got))
            elements.extend(got)
        except Exception as e:
            logger.warning('Overpass water query failed: %s', e)

    seen_ids = set()
    seen_lakes = set()
    for el in elements:
        tags = el.get('tags') or {}
        name = tags.get('name') or tags.get('name:en') or tags.get('name:nl')
        if not name:
            continue
        key = (el.get('type'), el.get('id'))
        if key in seen_ids:
            continue
        seen_ids.add(key)
        kind = 'lake' if (tags.get('natural') == 'water' or tags.get('water') == 'lake' or el.get('bounds')) else 'river'
        if tags.get('waterway') == 'river':
            kind = 'river'
        geom = _line_from_el(el)
        bbox = None
        if geom is None:
            geom, bbox = _poly_from_bounds(el)
        if geom is None:
            continue
        if kind == 'lake':
            if name.lower() in seen_lakes:
                continue
            seen_lakes.add(name.lower())
        records.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM water (Overpass)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='ODbL',
            geometry=geom,
            raw={
                'osm_id': el.get('id'),
                'osm_type': el.get('type'),
                'name': name,
                'kind': kind,
                'waterway': tags.get('waterway'),
                'bbox': bbox,
                'tags': {k: tags[k] for k in ('name', 'name:en', 'name:nl', 'name:fr', 'waterway', 'natural', 'water') if k in tags},
            },
        ))

    have_rivers = any((r.raw or {}).get('kind') == 'river' for r in records)
    if not have_rivers:
        logger.warning('no live rivers; appending named-river fixtures')
        for rec in _fixtures():
            if rec.raw.get('kind') == 'river':
                records.append(rec)
    if not records:
        logger.warning('using named-water fixture')
        return _fixtures()
    logger.info('water features: %s', len(records))
    return records
