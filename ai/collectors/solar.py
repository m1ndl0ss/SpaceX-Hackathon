"""OSM solar generators / plants."""
from collectors.base import CollectedRecord, now_iso
from collectors import overpass
from collectors.region import OVERPASS_BBOX

SOURCE_ID = 'E002'
QL = f"""
[out:json][timeout:45];
(
  nwr["plant:source"="solar"]({OVERPASS_BBOX});
  node["generator:source"="solar"]["generator:output:electricity"]({OVERPASS_BBOX});
);
out center tags;
"""


def collect_all():
    try:
        data = overpass.query(QL)
        elements = data.get('elements') or []
    except Exception as e:
        print(f'  solar overpass failed, using fixtures: {e}')
        elements = []
    recs = []
    for el in elements:
        pt = overpass.point(el)
        if not pt:
            continue
        tags = el.get('tags') or {}
        recs.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM solar',
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
        if len(recs) >= 400:
            break
    if not recs:
        print('  solar empty, using fixtures')
        recs = _fixtures()
    return recs


def _fixtures():
    sites = [
        (5.29, 51.70, 'Noord-Brabant solar (fixture)'),
        (4.40, 51.22, 'Antwerp solar (fixture)'),
        (6.13, 49.61, 'Luxembourg solar (fixture)'),
        (5.69, 50.85, 'Maastricht solar (fixture)'),
    ]
    recs = []
    for lon, lat, name in sites:
        recs.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM solar',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='fixture',
            geometry={'type': 'Point', 'coordinates': [lon, lat]},
            raw={'name': name, 'generator:source': 'solar'},
        ))
    return recs
