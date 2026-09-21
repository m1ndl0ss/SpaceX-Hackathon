"""Overpass pull of major roads in Benelux. Cached for demo."""
import logging

from collectors.base import CollectedRecord, now_iso
from collectors import overpass

logger = logging.getLogger(__name__)

SOURCE_ID = 'S005'
QUERIES = [
    '[out:json][timeout:20];way["highway"="motorway"](50.75,5.55,50.95,5.80);out geom 15;',
    '[out:json][timeout:20];way["highway"="motorway"](51.10,4.25,51.30,4.50);out geom 15;',
    '[out:json][timeout:20];way["highway"="motorway"](49.55,6.05,49.75,6.25);out geom 10;',
    '[out:json][timeout:20];way["highway"="motorway"](52.00,5.00,52.20,5.30);out geom 10;',
]


def _fixtures():
    return [
        {'id': 1, 'tags': {'name': 'A2', 'highway': 'motorway', 'ref': 'A2'}, 'geometry': [
            {'lon': 5.690, 'lat': 50.851}, {'lon': 5.480, 'lat': 51.440}, {'lon': 5.120, 'lat': 52.090}
        ]},
        {'id': 2, 'tags': {'name': 'E40', 'highway': 'motorway', 'ref': 'E40'}, 'geometry': [
            {'lon': 2.80, 'lat': 50.85}, {'lon': 4.35, 'lat': 50.85}, {'lon': 5.60, 'lat': 50.82}
        ]},
        {'id': 3, 'tags': {'name': 'A3', 'highway': 'motorway', 'ref': 'A3'}, 'geometry': [
            {'lon': 6.131, 'lat': 49.611}, {'lon': 6.170, 'lat': 49.800}
        ]},
        {'id': 4, 'tags': {'name': 'A12', 'highway': 'trunk', 'ref': 'A12'}, 'geometry': [
            {'lon': 4.402, 'lat': 51.219}, {'lon': 4.350, 'lat': 51.450}
        ]},
    ]


def _records_from_elements(elements, license_id):
    records = []
    for el in elements:
        geom = el.get('geometry') or []
        if len(geom) < 2:
            continue
        coords = [[p['lon'], p['lat']] for p in geom]
        records.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM roads (Overpass)' if license_id == 'ODbL' else 'OSM roads (fixture)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license=license_id,
            geometry={'type': 'LineString', 'coordinates': coords},
            raw={'osm_id': el.get('id'), 'tags': el.get('tags', {})},
        ))
    return records


def collect_all():
    elements = []
    for i, ql in enumerate(QUERIES):
        try:
            data = overpass.query(ql)
            got = data.get('elements') or []
            logger.info('Overpass road query %s returned %s elements', i, len(got))
            elements.extend(got)
        except Exception as e:
            logger.warning('Overpass road query %s failed: %s', i, e)
    records = _records_from_elements(elements, 'ODbL')
    if not records:
        logger.warning('no live road geometries; using named-road fixture')
        records = _records_from_elements(_fixtures(), 'fixture')
    logger.info('OSM road segments: %s', len(records))
    return records
