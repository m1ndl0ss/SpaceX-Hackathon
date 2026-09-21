"""Leftover Italy briefing fixtures. Not in COLLECTORS — news is not training labels."""
from collectors.base import CollectedRecord, now_iso

SOURCE_ID = 'C005'

FIXTURES = [
    {
        'title': 'Orso marsicano avvistato nei pressi di Pescasseroli',
        'url': 'https://example.local/fixture/pescasseroli-sighting',
        'summary': 'Avvistamento confermato di Ursus arctos marsicanus vicino all\'abitato.',
        'lat': 41.81, 'lon': 13.79,
    },
    {
        'title': 'Incidente stradale con fauna selvatica sulla SS83',
        'url': 'https://example.local/fixture/ss83-collision',
        'summary': 'Veicolo coinvolto in collisione notturna; specie da verificare.',
        'lat': 41.84, 'lon': 13.82,
    },
]


def collect_all():
    recs = []
    for f in FIXTURES:
        recs.append(CollectedRecord(
            source_id=SOURCE_ID,
            source_name='News fixtures (GDELT/RSS stand-in)',
            source_url=f['url'],
            collected_at=now_iso(),
            license='fixture',
            geometry={'type': 'Point', 'coordinates': [f['lon'], f['lat']]},
            raw=f,
        ))
    return recs
