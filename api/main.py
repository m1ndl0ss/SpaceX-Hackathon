import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).parent.parent
RAW = ROOT / 'data' / 'raw'
SCORES = ROOT / 'data' / 'scores'
CACHE = ROOT / 'data' / 'cache'

app = FastAPI(title='Bear tracker data API', version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['GET'],
    allow_headers=['*'],
)


def _json(path: Path):
    if not path.exists():
        raise HTTPException(404, f'missing cache {path.name} — run python run.py')
    return json.loads(path.read_text(encoding='utf-8'))


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/sources')
def sources():
    files = sorted(p.name for p in RAW.glob('*_latest.json'))
    return {
        'cached': files,
        'catalog': [
            {'id': 'C001', 'name': 'GBIF', 'role': 'collect'},
            {'id': 'S001', 'name': 'Protected areas (fixture clip)', 'role': 'score'},
            {'id': 'S004', 'name': 'Open-Meteo', 'role': 'score'},
            {'id': 'S005', 'name': 'OSM roads', 'role': 'score'},
            {'id': 'C005', 'name': 'News fixtures', 'role': 'collect'},
        ],
    }


@app.get('/occurrences')
def occurrences():
    return _json(RAW / 'gbif_latest.json')


@app.get('/weather')
def weather():
    return _json(RAW / 'open_meteo_latest.json')


@app.get('/roads')
def roads():
    return _json(RAW / 'osm_roads_latest.json')


@app.get('/protected-areas')
def protected_areas():
    return _json(RAW / 'protected_areas_latest.json')


@app.get('/news')
def news():
    return _json(RAW / 'news_latest.json')


@app.get('/scores')
def scores():
    return _json(SCORES / 'cells_latest.json')


@app.get('/cache')
def frontend_cache():
    return _json(CACHE / 'frontend_latest.json')
