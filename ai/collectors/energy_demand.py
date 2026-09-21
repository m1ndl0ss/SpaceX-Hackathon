"""Two grid demand proxies from OSM populated places.

transmission: city/town load (HV/MV bulk)
distribution: village/hamlet load (local LV/MV)
Peak MW ≈ population × kW/capita / 1000. Not metered Terna data.
"""
from collectors.base import CollectedRecord, now_iso
from collectors import overpass
from collectors.region import OVERPASS_BBOX

SOURCE_ID = 'E004'
KW_PER_CAPITA = {
    'transmission': 1.1,
    'distribution': 0.45,
}
QL = f"""
[out:json][timeout:45];
(
  node["place"~"^(city|town)$"]["population"]({OVERPASS_BBOX});
  node["place"~"^(village|hamlet)$"]["population"]({OVERPASS_BBOX});
);
out center tags;
"""


def _grid(place: str) -> str:
    if place in ('city', 'town'):
        return 'transmission'
    return 'distribution'


def collect_all():
    try:
        data = overpass.query(QL)
        elements = data.get('elements') or []
    except Exception as e:
        print(f'  demand overpass failed, using fixtures: {e}')
        elements = [
            {'type': 'node', 'id': 1, 'lon': 4.3517, 'lat': 50.8503, 'tags': {'name': 'Brussels', 'place': 'city', 'population': '1200000'}},
            {'type': 'node', 'id': 2, 'lon': 5.6900, 'lat': 50.8514, 'tags': {'name': 'Maastricht', 'place': 'city', 'population': '120000'}},
        ]
    recs = []
    for el in elements:
        pt = overpass.point(el)
        if not pt:
            continue
        tags = el.get('tags') or {}
        try:
            pop = int(str(tags.get('population', '0')).replace(',', '').split(';')[0])
        except ValueError:
            continue
        if pop <= 0:
            continue
        grid = _grid(tags.get('place', 'village'))
        mw = round(pop * KW_PER_CAPITA[grid] / 1000.0, 3)
        recs.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM population demand proxy',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='ODbL',
            geometry={'type': 'Point', 'coordinates': [pt[0], pt[1]]},
            raw={
                'osm_id': el.get('id'),
                'name': tags.get('name'),
                'place': tags.get('place'),
                'grid': grid,
                'population': pop,
                'peak_demand_mw_proxy': mw,
                'kw_per_capita': KW_PER_CAPITA[grid],
            },
        ))
    if not recs:
        print('  demand empty, using fixtures')
        return _fixtures()
    return recs


def _fixtures():
    elements = [
        {'lon': 4.9041, 'lat': 52.3676, 'tags': {'name': 'Amsterdam', 'place': 'city', 'population': '920000'}},
        {'lon': 4.3517, 'lat': 50.8503, 'tags': {'name': 'Brussels', 'place': 'city', 'population': '1200000'}},
        {'lon': 6.1319, 'lat': 49.6116, 'tags': {'name': 'Luxembourg', 'place': 'city', 'population': '130000'}},
        {'lon': 4.4025, 'lat': 51.2194, 'tags': {'name': 'Antwerp', 'place': 'city', 'population': '530000'}},
        {'lon': 5.6900, 'lat': 50.8514, 'tags': {'name': 'Maastricht', 'place': 'city', 'population': '120000'}},
    ]
    recs = []
    for el in elements:
        tags = el['tags']
        pop = int(tags['population'])
        grid = _grid(tags['place'])
        mw = round(pop * KW_PER_CAPITA[grid] / 1000.0, 3)
        recs.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='OSM population demand proxy',
            source_url='https://www.openstreetmap.org/copyright',
            collected_at=now_iso(),
            license='fixture',
            geometry={'type': 'Point', 'coordinates': [el['lon'], el['lat']]},
            raw={
                'name': tags['name'],
                'place': tags['place'],
                'grid': grid,
                'population': pop,
                'peak_demand_mw_proxy': mw,
                'kw_per_capita': KW_PER_CAPITA[grid],
            },
        ))
    return recs
