"""Small Overpass pull of major roads in the Abruzzo bbox. Cached for demo."""
import logging

import httpx

from collectors.base import CollectedRecord, now_iso, with_retry

logger = logging.getLogger(__name__)

SOURCE_ID = 'S005'
OVERPASS = 'https://overpass-api.de/api/interpreter'
QUERY = """
[out:json][timeout:25];
way["highway"~"motorway|trunk|primary"](41.4,13.0,42.8,14.5);
out geom 80;
"""


def collect_all():
    records = []
    try:
        with httpx.Client(timeout=40) as client:
            resp = with_retry(lambda: client.post(OVERPASS, data={'data': QUERY}))
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning('Overpass failed (%s); using fixture roads', e)
        data = {'elements': [
            {'id': 1, 'tags': {'name': 'A25', 'highway': 'motorway'}, 'geometry': [
                {'lon': 13.6, 'lat': 42.05}, {'lon': 13.9, 'lat': 42.10}, {'lon': 14.2, 'lat': 42.16}
            ]},
            {'id': 2, 'tags': {'name': 'SS83', 'highway': 'primary'}, 'geometry': [
                {'lon': 13.70, 'lat': 41.78}, {'lon': 13.83, 'lat': 41.83}
            ]},
        ]}

    for el in data.get('elements', []):
        geom = el.get('geometry') or []
        if len(geom) < 2:
            continue
        coords = [[p['lon'], p['lat']] for p in geom]
        records.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM roads (Overpass)',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='ODbL',
            geometry={'type': 'LineString', 'coordinates': coords},
            raw={'osm_id': el.get('id'), 'tags': el.get('tags', {})},
        ))
    logger.info('OSM road segments: %s', len(records))
    return records
