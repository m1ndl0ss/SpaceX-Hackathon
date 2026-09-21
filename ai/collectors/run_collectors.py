import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collectors import (
    habitats,
    open_meteo,
    osm_roads,
    protected_areas,
    roadkill,
    water,
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

OUTPUT_DIR = Path(__file__).resolve().parents[2] / 'data'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Energy Overpass layers skipped to keep collect runs under rate limits.
# News is briefing-only and is not collected (Italy fixtures would pollute the cache).
COLLECTORS = [
    ('habitats', habitats.collect_all),
    ('roadkill', roadkill.collect_all),
    ('protected_areas', protected_areas.collect_all),
    ('open_meteo', open_meteo.collect_all),
    ('osm_roads', osm_roads.collect_all),
    ('water', water.collect_all),
]

STALE_ITALY = [
    'news_latest.json',
    'wind_latest.json',
    'solar_latest.json',
    'substations_latest.json',
    'energy_demand_latest.json',
    'gbif_latest.json',
    'cells_latest.json',
    'frontend_latest.json',
]


def save(name, records):
    payload = [r.to_dict() for r in records]
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    (OUTPUT_DIR / f'{name}_latest.json').write_text(text, encoding='utf-8')
    return len(payload)


def _clear_stale():
    for name in STALE_ITALY:
        path = OUTPUT_DIR / name
        if path.exists():
            path.unlink()
            print(f'  removed stale {name}')


def _write_sources(results):
    catalog = {
        'region': 'Benelux (NL, BE, LU)',
        'bbox': [2.3, 49.4, 7.3, 53.7],
        'files': results,
        'catalog': [
            {'id': 'C001', 'name': 'GBIF habitats (Benelux species)', 'file': 'habitats_latest.json', 'role': 'collect'},
            {'id': 'C006', 'name': 'GBIF Global Roadkill Data (Grilo 2025)', 'file': 'roadkill_latest.json', 'role': 'collect'},
            {'id': 'S001', 'name': 'EEA Natura 2000 (NL/BE/LU)', 'file': 'protected_areas_latest.json', 'role': 'collect'},
            {'id': 'S004', 'name': 'Open-Meteo monthly climatology', 'file': 'open_meteo_latest.json', 'role': 'collect'},
            {'id': 'S005', 'name': 'OSM roads (Overpass, cached)', 'file': 'osm_roads_latest.json', 'role': 'collect'},
            {'id': 'C007', 'name': 'OSM water (rivers/lakes, cached)', 'file': 'water_latest.json', 'role': 'collect'},
        ],
        'notes': {
            'scoring': 'Abruzzo bear composite in scoring/engine.py is stale and not run by default.',
            'energy': 'Wind/solar/substations/demand collectors exist but are skipped (Overpass budget).',
            'news': 'GDELT/news is briefing-only and is not collected.',
        },
    }
    (OUTPUT_DIR / 'sources_latest.json').write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8'
    )


def main():
    _clear_stale()
    results = []
    for i, (name, fn) in enumerate(COLLECTORS):
        print(f'--- {name} ---')
        try:
            recs = fn()
            n = save(name, recs)
            licenses = sorted({(r.license or 'unknown') for r in recs})
            print(f'  saved {n} licenses={licenses}')
            results.append({'name': name, 'file': f'{name}_latest.json', 'records': n, 'licenses': licenses, 'ok': True})
        except Exception as e:
            logging.error('%s failed: %s', name, e)
            print(f'  ERROR {e}')
            results.append({'name': name, 'file': f'{name}_latest.json', 'records': 0, 'ok': False, 'error': str(e)})
        if i < len(COLLECTORS) - 1:
            time.sleep(3)
    _write_sources(results)


if __name__ == '__main__':
    main()
