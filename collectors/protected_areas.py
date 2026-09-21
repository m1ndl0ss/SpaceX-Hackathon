"""Fixture clip of Marsican bear core parks. Stands in for a Natura 2000 extract."""
from collectors.base import CollectedRecord, now_iso

SOURCE_ID = 'S001'

# Approximate polygons for demo / scoring. Not official Natura 2000 geometry.
AREAS = [
    {
        'id': 'PNALM',
        'name': 'Parco Nazionale d\'Abruzzo, Lazio e Molise',
        'kind': 'national_park',
        'bbox': [13.55, 41.68, 14.05, 41.95],
    },
    {
        'id': 'MAIELLA',
        'name': 'Parco Nazionale della Maiella',
        'kind': 'national_park',
        'bbox': [13.90, 41.95, 14.35, 42.25],
    },
    {
        'id': 'SIRENTE',
        'name': 'Parco Naturale Regionale Sirente-Velino',
        'kind': 'regional_park',
        'bbox': [13.35, 42.05, 13.80, 42.30],
    },
]


def _box_poly(b):
    minx, miny, maxx, maxy = b
    ring = [[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]
    return {'type': 'Polygon', 'coordinates': [ring]}


def collect_all():
    recs = []
    for a in AREAS:
        recs.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='Protected area fixtures (Natura 2000 stand-in)',
            source_url='https://www.eea.europa.eu/en/datahub/datahubitem-view/6fc8ad2d-195d-40f4-bdec-576e7d1268e4',
            collected_at=now_iso(),
            license='fixture',
            geometry=_box_poly(a['bbox']),
            raw=a,
        ))
    return recs
