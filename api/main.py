import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

app = FastAPI(title='Benelux wildlife data API', version='0.2.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['GET'],
    allow_headers=['*'],
)


def _json(path: Path):
    if not path.exists():
        raise HTTPException(404, f'missing cache {path.name} — run python run.py --collect-only')
    return json.loads(path.read_text(encoding='utf-8'))


@app.get('/health')
def health():
    return {'status': 'ok', 'region': 'Benelux', 'bbox': [2.3, 49.4, 7.3, 53.7]}


@app.get('/sources')
def sources():
    catalog_path = DATA / 'sources_latest.json'
    if catalog_path.exists():
        return _json(catalog_path)
    files = sorted(p.name for p in DATA.glob('*_latest.json'))
    return {
        'cached': files,
        'region': 'Benelux (NL, BE, LU)',
        'catalog': [
            {'id': 'C001', 'name': 'GBIF habitats (Benelux species)', 'role': 'collect'},
            {'id': 'C006', 'name': 'GBIF Global Roadkill Data (Grilo 2025)', 'role': 'collect'},
            {'id': 'S001', 'name': 'EEA Natura 2000 (NL/BE/LU)', 'role': 'collect'},
            {'id': 'S004', 'name': 'Open-Meteo monthly climatology', 'role': 'collect'},
            {'id': 'S005', 'name': 'OSM roads', 'role': 'collect'},
            {'id': 'C007', 'name': 'OSM water', 'role': 'collect'},
        ],
    }


@app.get('/habitats')
def habitats():
    return _json(DATA / 'habitats_latest.json')


@app.get('/roads')
def roads():
    return _json(DATA / 'osm_roads_latest.json')


@app.get('/protected-areas')
def protected_areas():
    return _json(DATA / 'protected_areas_latest.json')


@app.get('/weather')
def weather():
    return _json(DATA / 'open_meteo_latest.json')


@app.get('/roadkill')
def roadkill():
    return _json(DATA / 'roadkill_latest.json')


@app.get('/water')
def water():
    return _json(DATA / 'water_latest.json')
