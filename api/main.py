"""Benelux wildlife data API plus demo persistence.

GIS overlays stay as files (data/*_latest.json and data/cached/).
User-created rows live in SQLite (data/app.db), seeded from data/seed/catalog.json.

Run: uvicorn api.main:app --port 8000 --reload

Frontend (app/ is empty in this repo; drop this into state.js when it lands):

  const API = 'http://localhost:8000'
  const auth = (token) => ({ Authorization: `Bearer ${token}` })

  POST /auth/people  { name, place, help, status?, hours? }
  POST /auth/org     { name?, place?, help?, org?, type? }   // defaults Alex Morgan / South Holland
  GET  /users/me     Authorization: Bearer <token>           // profile + joined opportunity ids
  GET  /users        people roster (merged with org accounts)
  GET  /users/{id}

  GET  /opportunities
  POST /opportunities/{id}/join   body optional { user_id } or Bearer token
  POST /opportunities/{id}/leave

  GET/POST /reports               { place, note, status?, who?, lng?, lat? }
  PATCH    /reports/{id}          { status }

  GET  /activity
  GET  /sites  /partners  /lookups  /stats  /health
  GET/POST /projects
  GET/POST /projects/{id}/scenarios   { comparison, inputs, results, name? }
  GET/POST /response-drafts           { site, type, partner_id?, people_id? }

Do not persist screen, selected site index, overlay theme, layer checkboxes,
dirty flag, live sliders before Run, or map view — those stay client-only.
"""
import json
from pathlib import Path

from fastapi import Body, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api import db

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

app = FastAPI(title='Benelux wildlife data API', version='0.3.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def startup():
    db.init_db()


def _json(path: Path):
    if not path.exists():
        raise HTTPException(404, f'missing cache {path.name} — run python run.py --collect-only')
    return json.loads(path.read_text(encoding='utf-8'))


def _bearer(authorization: str | None):
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        return parts[1].strip()
    return authorization.strip()


def _require_user(conn, authorization: str | None, user_id: str | None = None):
    token = _bearer(authorization)
    row = db.get_user(conn, user_id=user_id, token=token)
    if row is None and user_id and token:
        row = db.get_user(conn, user_id=user_id)
    if row is None:
        raise HTTPException(401, 'sign in via POST /auth/people or POST /auth/org')
    return row


class PeopleAuthIn(BaseModel):
    name: str
    place: str
    help: str = 'survey'
    status: str = 'New'
    hours: int = 0


class OrgAuthIn(BaseModel):
    name: str = 'Alex Morgan'
    place: str = 'Dordrecht'
    help: str = 'survey'
    org: str = 'South Holland'
    type: str = 'municipality'


class UserRefIn(BaseModel):
    user_id: str | None = None


class ReportIn(BaseModel):
    place: str
    note: str
    status: str | None = None
    who: str | None = None
    lng: float | None = None
    lat: float | None = None
    user_id: str | None = None


class ReportStatusIn(BaseModel):
    status: str


class ProjectIn(BaseModel):
    name: str
    label: str | None = None
    lng: float | None = None
    lat: float | None = None
    coords: list[float] | None = None


class ScenarioIn(BaseModel):
    comparison: str
    inputs: dict
    results: dict
    name: str | None = None


class DraftIn(BaseModel):
    site: str
    type: str
    partner_id: str | None = None
    people_id: str | None = None
    createdAt: str | None = None


@app.get('/health')
def health():
    return {
        'status': 'ok',
        'region': 'Benelux',
        'bbox': [2.3, 49.4, 7.3, 53.7],
        'db': str(db.DB_PATH.name),
        'persist': True,
    }


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


@app.post('/auth/people')
def auth_people(payload: PeopleAuthIn):
    conn = db.connect()
    try:
        row, created = db.upsert_people(
            conn,
            name=payload.name,
            place=payload.place,
            help=payload.help,
            status=payload.status,
            hours=payload.hours,
        )
        conn.commit()
        return {**db.profile(conn, row), 'created': created}
    finally:
        conn.close()


@app.post('/auth/org')
def auth_org(payload: OrgAuthIn | None = Body(None)):
    payload = payload or OrgAuthIn()
    conn = db.connect()
    try:
        row, created = db.upsert_org(
            conn,
            name=payload.name,
            place=payload.place,
            help=payload.help,
            org=payload.org,
            type=payload.type,
        )
        conn.commit()
        return {**db.profile(conn, row), 'created': created}
    finally:
        conn.close()


@app.get('/users/me')
def users_me(authorization: str | None = Header(None), token: str | None = Query(None)):
    conn = db.connect()
    try:
        row = db.get_user(conn, token=_bearer(authorization) or token)
        if not row:
            raise HTTPException(401, 'sign in via POST /auth/people or POST /auth/org')
        return db.profile(conn, row)
    finally:
        conn.close()


@app.get('/users/{user_id}')
def users_get(user_id: str):
    conn = db.connect()
    try:
        row = db.get_user(conn, user_id=user_id)
        if not row:
            raise HTTPException(404, 'user not found')
        return db.user_public(row, joined=db.user_joined(conn, row['id']))
    finally:
        conn.close()


@app.get('/users')
def users_list():
    conn = db.connect()
    try:
        return db.list_users(conn)
    finally:
        conn.close()


@app.get('/sites')
def sites_list():
    conn = db.connect()
    try:
        return db.list_sites(conn)
    finally:
        conn.close()


@app.get('/partners')
def partners_list():
    conn = db.connect()
    try:
        return db.list_partners(conn)
    finally:
        conn.close()


@app.get('/lookups')
def lookups_get():
    conn = db.connect()
    try:
        return db.lookups(conn)
    finally:
        conn.close()


@app.get('/stats')
def stats_get():
    conn = db.connect()
    try:
        return db.stats(conn)
    finally:
        conn.close()


@app.get('/opportunities')
def opportunities_list():
    conn = db.connect()
    try:
        return db.list_opportunities(conn)
    finally:
        conn.close()


@app.post('/opportunities/{opportunity_id}/join')
def opportunities_join(
    opportunity_id: str,
    payload: UserRefIn | None = Body(None),
    authorization: str | None = Header(None),
):
    conn = db.connect()
    try:
        user = _require_user(conn, authorization, payload.user_id if payload else None)
        try:
            result = db.join_opportunity(conn, user['id'], opportunity_id)
        except KeyError as e:
            raise HTTPException(404, str(e)) from e
        if result == 'full':
            raise HTTPException(409, 'no spots left')
        if result == 'exists':
            raise HTTPException(409, 'already joined')
        return {
            'ok': True,
            'joined': db.user_joined(conn, user['id']),
            'opportunity': db.opp_public(
                conn.execute('SELECT * FROM opportunities WHERE id = ?', (opportunity_id,)).fetchone()
            ),
        }
    finally:
        conn.close()


@app.post('/opportunities/{opportunity_id}/leave')
def opportunities_leave(
    opportunity_id: str,
    payload: UserRefIn | None = Body(None),
    authorization: str | None = Header(None),
):
    conn = db.connect()
    try:
        user = _require_user(conn, authorization, payload.user_id if payload else None)
        try:
            result = db.leave_opportunity(conn, user['id'], opportunity_id)
        except KeyError as e:
            raise HTTPException(404, str(e)) from e
        if result == 'missing':
            raise HTTPException(404, 'not joined')
        return {
            'ok': True,
            'joined': db.user_joined(conn, user['id']),
            'opportunity': db.opp_public(
                conn.execute('SELECT * FROM opportunities WHERE id = ?', (opportunity_id,)).fetchone()
            ),
        }
    finally:
        conn.close()


@app.get('/reports')
def reports_list():
    conn = db.connect()
    try:
        return db.list_reports(conn)
    finally:
        conn.close()


@app.post('/reports')
def reports_create(payload: ReportIn, authorization: str | None = Header(None)):
    conn = db.connect()
    try:
        user_id = payload.user_id
        token = _bearer(authorization)
        if token:
            row = db.get_user(conn, token=token)
            if row:
                user_id = row['id']
        return db.create_report(
            conn,
            place=payload.place,
            note=payload.note,
            status=payload.status,
            who=payload.who,
            lng=payload.lng,
            lat=payload.lat,
            user_id=user_id,
        )
    finally:
        conn.close()


@app.patch('/reports/{report_id}')
def reports_patch(report_id: str, payload: ReportStatusIn):
    conn = db.connect()
    try:
        return db.patch_report(conn, report_id, payload.status)
    except KeyError:
        raise HTTPException(404, 'report not found')
    except ValueError:
        raise HTTPException(400, f'status must be one of {list(db.REPORT_STATUSES)}')
    finally:
        conn.close()


@app.get('/activity')
def activity_list(limit: int = 50):
    conn = db.connect()
    try:
        return db.list_activity(conn, limit=min(limit, 200))
    finally:
        conn.close()


@app.get('/projects')
def projects_list():
    conn = db.connect()
    try:
        return db.list_projects(conn)
    finally:
        conn.close()


@app.post('/projects')
def projects_create(payload: ProjectIn):
    lng, lat = payload.lng, payload.lat
    if payload.coords and len(payload.coords) >= 2:
        lng, lat = payload.coords[0], payload.coords[1]
    conn = db.connect()
    try:
        return db.create_project(conn, name=payload.name, label=payload.label, lng=lng, lat=lat)
    finally:
        conn.close()


@app.get('/projects/{project_id}/scenarios')
def scenarios_list(project_id: str):
    conn = db.connect()
    try:
        if not db.get_project(conn, project_id):
            raise HTTPException(404, 'project not found')
        return db.list_scenarios(conn, project_id)
    finally:
        conn.close()


@app.post('/projects/{project_id}/scenarios')
def scenarios_create(project_id: str, payload: ScenarioIn):
    conn = db.connect()
    try:
        if not db.get_project(conn, project_id):
            raise HTTPException(404, 'project not found')
        return db.create_scenario(
            conn,
            project_id,
            comparison=payload.comparison,
            inputs=payload.inputs,
            results=payload.results,
            name=payload.name,
        )
    except ValueError:
        raise HTTPException(400, f'comparison must be one of {list(db.COMPARISONS)}')
    finally:
        conn.close()


@app.get('/response-drafts')
def drafts_list():
    conn = db.connect()
    try:
        return db.list_drafts(conn)
    finally:
        conn.close()


@app.post('/response-drafts')
def drafts_create(payload: DraftIn):
    conn = db.connect()
    try:
        return db.create_draft(
            conn,
            site=payload.site,
            type=payload.type,
            partner_id=payload.partner_id,
            people_id=payload.people_id,
        )
    except KeyError:
        raise HTTPException(404, 'site not found — use site id, not array index')
    finally:
        conn.close()
