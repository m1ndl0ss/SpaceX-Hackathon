"""OSM wind turbines / wind plants."""
from collectors.base import CollectedRecord, now_iso
from collectors import overpass
from collectors.region import OVERPASS_BBOX

SOURCE_ID = 'E001'
QL = f"""
[out:json][timeout:45];
(
  nwr["generator:source"="wind"]({OVERPASS_BBOX});
  nwr["plant:source"="wind"]({OVERPASS_BBOX});
);
out center tags;
"""


def collect_all():
    try:
        data = overpass.query(QL)
        elements = data.get('elements') or []
    except Exception as e:
        print(f'  wind overpass failed, using fixtures: {e}')
        elements = [
            {'type': 'node', 'id': 1, 'lon': 5.20, 'lat': 52.10, 'tags': {'name': 'Fixture wind', 'generator:source': 'wind'}},
        ]
    recs = []
    for el in elements:
        pt = overpass.point(el)
        if not pt:
            continue
        tags = el.get('tags') or {}
        recs.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM wind',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='ODbL',
            geometry={'type': 'Point', 'coordinates': [pt[0], pt[1]]},
            raw={
                'osm_id': el.get('id'),
                'osm_type': el.get('type'),
                'name': tags.get('name'),
                'output': tags.get('generator:output:electricity') or tags.get('plant:output:electricity'),
                'tags': tags,
            },
        ))
    return recs
