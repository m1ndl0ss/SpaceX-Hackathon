"""OSM substations as energy distribution / transmission hubs."""
from collectors.base import CollectedRecord, now_iso
from collectors import overpass
from collectors.region import OVERPASS_BBOX

SOURCE_ID = 'E003'
QL = f"""
[out:json][timeout:45];
nwr["power"="substation"]({OVERPASS_BBOX});
out center tags;
"""


def _role(tags: dict) -> str:
    kind = (tags.get('substation') or '').lower()
    if kind in ('transmission', 'distribution', 'industrial', 'traction', 'minor_distribution'):
        return kind
    voltage = tags.get('voltage') or ''
    try:
        kv = int(str(voltage).split(';')[0]) / 1000
        if kv >= 150:
            return 'transmission'
        if kv >= 30:
            return 'distribution'
    except ValueError:
        pass
    return 'unknown'


def collect_all():
    try:
        data = overpass.query(QL)
        elements = data.get('elements') or []
    except Exception as e:
        print(f'  substations overpass failed, using fixtures: {e}')
        elements = [
            {'type': 'node', 'id': 1, 'lon': 5.11, 'lat': 52.09, 'tags': {'name': 'Fixture 380 kV', 'power': 'substation', 'substation': 'transmission', 'voltage': '380000'}},
            {'type': 'node', 'id': 2, 'lon': 4.35, 'lat': 50.85, 'tags': {'name': 'Fixture 20 kV', 'power': 'substation', 'substation': 'distribution', 'voltage': '20000'}},
        ]
    recs = []
    for el in elements:
        pt = overpass.point(el)
        if not pt:
            continue
        tags = el.get('tags') or {}
        recs.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM substations',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='ODbL',
            geometry={'type': 'Point', 'coordinates': [pt[0], pt[1]]},
            raw={
                'osm_id': el.get('id'),
                'osm_type': el.get('type'),
                'name': tags.get('name'),
                'grid_role': _role(tags),
                'voltage': tags.get('voltage'),
                'operator': tags.get('operator'),
                'tags': tags,
            },
        ))
    return recs
