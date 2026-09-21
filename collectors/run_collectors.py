import json
import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors import gbif, news, open_meteo, osm_roads, protected_areas

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'raw'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TODAY = date.today().isoformat()

COLLECTORS = [
    ('gbif', gbif.collect_all),
    ('open_meteo', open_meteo.collect_all),
    ('protected_areas', protected_areas.collect_all),
    ('osm_roads', osm_roads.collect_all),
    ('news', news.collect_all),
]


def save(name, records):
    payload = [r.to_dict() for r in records]
    path = OUTPUT_DIR / f'{name}_{TODAY}.json'
    latest = OUTPUT_DIR / f'{name}_latest.json'
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(text, encoding='utf-8')
    latest.write_text(text, encoding='utf-8')
    return len(payload)


def main():
    for name, fn in COLLECTORS:
        print(f'--- {name} ---')
        try:
            recs = fn()
            n = save(name, recs)
            print(f'  saved {n}')
        except Exception as e:
            logging.error('%s failed: %s', name, e)
            print(f'  ERROR {e}')


if __name__ == '__main__':
    main()
