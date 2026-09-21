"""SQLite demo store. Seeded from data/seed/catalog.json when empty."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'
SEED_PATH = DATA / 'seed' / 'catalog.json'
DB_PATH = Path(os.environ.get('APP_DB', str(DATA / 'app.db')))

DEFAULT_PIN = (4.69, 51.805)
REPORT_STATUSES = (
    'Awaiting verification',
    'Field check assigned',
    'Verified',
    'Needs action',
)
VOLUNTEER_STATUSES = ('Active', 'Away', 'New')
HELP_OPTIONS = ('survey', 'restore', 'report', 'donate')
COMPARISONS = ('baseline', 'proposed', 'mitigated')
ORG_TYPES = ('municipality', 'ngo', 'university', 'company')

SCHEMA = """
CREATE TABLE IF NOT EXISTS organisations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  place TEXT,
  focus TEXT,
  people INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  place TEXT,
  help TEXT,
  org TEXT,
  org_id TEXT,
  type TEXT,
  role TEXT,
  status TEXT,
  hours INTEGER DEFAULT 0,
  token TEXT UNIQUE,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sites (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  action TEXT,
  species TEXT,
  note TEXT,
  lng REAL,
  lat REAL,
  value_min REAL,
  value_max REAL,
  funding_gap REAL,
  budget REAL,
  hectares REAL,
  description TEXT
);
CREATE TABLE IF NOT EXISTS opportunities (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  place TEXT,
  when_text TEXT,
  need TEXT,
  spots INTEGER DEFAULT 0,
  help TEXT
);
CREATE TABLE IF NOT EXISTS signups (
  user_id TEXT NOT NULL,
  opportunity_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (user_id, opportunity_id)
);
CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  place TEXT,
  note TEXT,
  status TEXT,
  who TEXT,
  time TEXT NOT NULL,
  lng REAL,
  lat REAL,
  user_id TEXT
);
CREATE TABLE IF NOT EXISTS activity_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  icon TEXT,
  tone TEXT,
  title TEXT,
  detail TEXT,
  time TEXT NOT NULL,
  kind TEXT NOT NULL,
  ref_id TEXT
);
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  label TEXT,
  lng REAL,
  lat REAL
);
CREATE TABLE IF NOT EXISTS scenarios (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT,
  comparison TEXT NOT NULL,
  inputs TEXT NOT NULL,
  results TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS response_drafts (
  id TEXT PRIMARY KEY,
  site TEXT NOT NULL,
  type TEXT NOT NULL,
  created_at TEXT NOT NULL,
  partner_id TEXT,
  people_id TEXT
);
CREATE TABLE IF NOT EXISTS lookups (
  kind TEXT NOT NULL,
  value TEXT NOT NULL,
  label TEXT
);
"""


def now_iso(dt=None):
    return (dt or datetime.now(timezone.utc)).isoformat()


def new_id(prefix='id'):
    return f'{prefix}-{uuid.uuid4().hex[:10]}'


def new_token():
    return uuid.uuid4().hex


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        _seed_if_empty(conn)
        conn.commit()
    finally:
        conn.close()


def _seed_if_empty(conn):
    n = conn.execute('SELECT COUNT(*) FROM sites').fetchone()[0]
    if n:
        return
    if not SEED_PATH.exists():
        return
    catalog = json.loads(SEED_PATH.read_text(encoding='utf-8'))
    t0 = datetime.now(timezone.utc)

    for region in catalog.get('lookups', {}).get('regions', []):
        conn.execute(
            'INSERT INTO lookups (kind, value, label) VALUES (?, ?, ?)',
            ('region', region, region),
        )
    for opt in catalog.get('lookups', {}).get('helpOptions', []):
        conn.execute(
            'INSERT INTO lookups (kind, value, label) VALUES (?, ?, ?)',
            ('help', opt['id'], opt.get('label') or opt['id']),
        )

    for org in catalog.get('partners', []):
        conn.execute(
            'INSERT INTO organisations (id, name, type, place, focus, people) VALUES (?,?,?,?,?,?)',
            (org['id'], org['name'], org['type'], org.get('place'), org.get('focus'), org.get('people') or 0),
        )
        _event(
            conn,
            icon='🤝',
            tone='info',
            title=f"{org['name']} on the network",
            detail=org.get('focus') or org['type'],
            time=now_iso(t0 - timedelta(hours=30)),
            kind='partner',
            ref_id=org['id'],
        )

    for person in catalog.get('people', []):
        conn.execute(
            '''INSERT INTO users (id, name, place, help, org, org_id, type, role, status, hours, token, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                person['id'], person['name'], person.get('place'), person.get('help'),
                person.get('org') or 'Independent', None, person.get('type') or 'person',
                person.get('role') or 'people', person.get('status') or 'New',
                int(person.get('hours') or 0), new_token(), now_iso(t0 - timedelta(days=4)),
            ),
        )

    for site in catalog.get('sites', []):
        lng, lat = _coords(site.get('coords'))
        vmin, vmax = _pair(site.get('valueRange'))
        conn.execute(
            '''INSERT INTO sites (id, name, action, species, note, lng, lat, value_min, value_max,
               funding_gap, budget, hectares, description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                site['id'], site['name'], site.get('action'), site.get('species'), site.get('note'),
                lng, lat, vmin, vmax, site.get('fundingGap'), site.get('budget'),
                site.get('hectares'), site.get('description'),
            ),
        )
    biggest = max(catalog.get('sites', []), key=lambda s: s.get('fundingGap') or 0, default=None)
    if biggest:
        _event(
            conn,
            icon='💶',
            tone='warn',
            title=f"€{int(biggest['fundingGap']):,} funding gap".replace(',', '.'),
            detail=biggest['name'],
            time=now_iso(t0 - timedelta(hours=20)),
            kind='funding',
            ref_id=biggest['id'],
        )

    for opp in catalog.get('opportunities', []):
        conn.execute(
            'INSERT INTO opportunities (id, title, place, when_text, need, spots, help) VALUES (?,?,?,?,?,?,?)',
            (opp['id'], opp['title'], opp.get('place'), opp.get('when'), opp.get('need'), opp.get('spots') or 0, opp.get('help')),
        )

    for signup in catalog.get('signups', []):
        _join_row(conn, signup['user_id'], signup['opportunity_id'], now_iso(t0 - timedelta(hours=8)), seed=True)

    for report in catalog.get('reports', []):
        lng, lat = report.get('lng'), report.get('lat')
        if lng is None or lat is None:
            lng, lat = DEFAULT_PIN
        when = now_iso(t0 - timedelta(hours=5))
        conn.execute(
            '''INSERT INTO reports (id, place, note, status, who, time, lng, lat, user_id)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (
                report['id'], report.get('place'), report.get('note'),
                report.get('status') or REPORT_STATUSES[0], report.get('who'),
                when, lng, lat, None,
            ),
        )
        _event(
            conn,
            icon='📍',
            tone='warn' if report.get('status') != 'Verified' else 'good',
            title=f"Field report · {report.get('place')}",
            detail=report.get('note') or '',
            time=when,
            kind='report',
            ref_id=report['id'],
        )

    for project in catalog.get('projects', []):
        lng, lat = _coords(project.get('coords'))
        conn.execute(
            'INSERT INTO projects (id, name, label, lng, lat) VALUES (?,?,?,?,?)',
            (project['id'], project['name'], project.get('label'), lng, lat),
        )


def _coords(value):
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return float(value[0]), float(value[1])
    return None, None


def _pair(value):
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return value[0], value[1]
    return None, None


def _event(conn, *, icon, tone, title, detail, time, kind, ref_id):
    conn.execute(
        '''INSERT INTO activity_events (icon, tone, title, detail, time, kind, ref_id)
           VALUES (?,?,?,?,?,?,?)''',
        (icon, tone, title, detail, time, kind, ref_id),
    )


def _join_row(conn, user_id, opportunity_id, created_at, seed=False):
    opp = conn.execute('SELECT * FROM opportunities WHERE id = ?', (opportunity_id,)).fetchone()
    if not opp:
        raise KeyError('opportunity')
    existing = conn.execute(
        'SELECT 1 FROM signups WHERE user_id = ? AND opportunity_id = ?',
        (user_id, opportunity_id),
    ).fetchone()
    if existing:
        return 'exists'
    spots = int(opp['spots'] or 0)
    if spots <= 0:
        return 'full'
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        raise KeyError('user')
    conn.execute(
        'INSERT INTO signups (user_id, opportunity_id, created_at) VALUES (?,?,?)',
        (user_id, opportunity_id, created_at),
    )
    conn.execute(
        'UPDATE opportunities SET spots = spots - 1 WHERE id = ? AND spots > 0',
        (opportunity_id,),
    )
    _event(
        conn,
        icon='🙋',
        tone='good',
        title=f"{user['name']} joined {opp['title']}",
        detail=opp['place'] or '',
        time=created_at,
        kind='join',
        ref_id=opportunity_id,
    )
    return 'ok'


def user_joined(conn, user_id):
    rows = conn.execute(
        'SELECT opportunity_id FROM signups WHERE user_id = ? ORDER BY created_at',
        (user_id,),
    ).fetchall()
    return [r['opportunity_id'] for r in rows]


def user_public(row, joined=None, token=False):
    if row is None:
        return None
    out = {
        'id': row['id'],
        'name': row['name'],
        'place': row['place'],
        'help': row['help'],
        'org': row['org'],
        'type': row['type'],
        'role': row['role'],
        'status': row['status'],
        'hours': row['hours'],
    }
    if joined is not None:
        out['joined'] = joined
    if token:
        out['token'] = row['token']
    return out


def _norm_help(value, default='survey'):
    if not value:
        return default
    v = str(value).strip().lower()
    return v if v in HELP_OPTIONS else default


def _norm_status(value, default='New'):
    if not value:
        return default
    for s in VOLUNTEER_STATUSES:
        if s.lower() == str(value).strip().lower():
            return s
    return default


def _norm_org_type(value, default='municipality'):
    if not value:
        return default
    v = str(value).strip().lower()
    aliases = {'ngo': 'ngo', 'n.g.o.': 'ngo', 'non-profit': 'ngo'}
    v = aliases.get(v, v)
    return v if v in ORG_TYPES else default


def get_user(conn, user_id=None, token=None):
    if token:
        return conn.execute('SELECT * FROM users WHERE token = ?', (token,)).fetchone()
    if user_id:
        return conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return None


def upsert_people(conn, *, name, place, help='survey', status='New', hours=0):
    help = _norm_help(help)
    status = _norm_status(status)
    hours = int(hours or 0)
    row = conn.execute(
        '''SELECT * FROM users WHERE role = 'people' AND lower(name) = lower(?) AND lower(place) = lower(?)''',
        (name, place),
    ).fetchone()
    if row:
        conn.execute(
            'UPDATE users SET help = ?, status = ?, hours = ? WHERE id = ?',
            (help, status, hours, row['id']),
        )
        row = conn.execute('SELECT * FROM users WHERE id = ?', (row['id'],)).fetchone()
        return row, False
    uid = new_id('u')
    conn.execute(
        '''INSERT INTO users (id, name, place, help, org, org_id, type, role, status, hours, token, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
        (uid, name.strip(), place.strip(), help, 'Independent', None, 'person', 'people', status, hours, new_token(), now_iso()),
    )
    return conn.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone(), True


def upsert_org(conn, *, name='Alex Morgan', place='Dordrecht', help='survey', org='South Holland', type='municipality'):
    help = _norm_help(help)
    org_type = _norm_org_type(type)
    org_row = conn.execute(
        'SELECT * FROM organisations WHERE lower(name) = lower(?)',
        (org,),
    ).fetchone()
    if org_row:
        org_id = org_row['id']
        conn.execute(
            'UPDATE organisations SET type = ?, place = COALESCE(place, ?) WHERE id = ?',
            (org_type, place, org_id),
        )
    else:
        org_id = new_id('org')
        conn.execute(
            'INSERT INTO organisations (id, name, type, place, focus, people) VALUES (?,?,?,?,?,?)',
            (org_id, org, org_type, place, None, 0),
        )
        _event(
            conn,
            icon='🤝',
            tone='info',
            title=f'{org} on the network',
            detail=org_type,
            time=now_iso(),
            kind='partner',
            ref_id=org_id,
        )
    row = conn.execute(
        '''SELECT * FROM users WHERE role = 'organisation' AND lower(name) = lower(?) AND lower(org) = lower(?)''',
        (name, org),
    ).fetchone()
    if row:
        conn.execute(
            'UPDATE users SET place = ?, help = ?, type = ?, org_id = ? WHERE id = ?',
            (place, help, org_type, org_id, row['id']),
        )
        return conn.execute('SELECT * FROM users WHERE id = ?', (row['id'],)).fetchone(), False
    uid = new_id('u')
    conn.execute(
        '''INSERT INTO users (id, name, place, help, org, org_id, type, role, status, hours, token, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
        (uid, name.strip(), place.strip(), help, org, org_id, org_type, 'organisation', None, 0, new_token(), now_iso()),
    )
    return conn.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone(), True


def profile(conn, row):
    return user_public(row, joined=user_joined(conn, row['id']), token=True)


def list_users(conn):
    rows = conn.execute("SELECT * FROM users ORDER BY role, name").fetchall()
    return [user_public(r, joined=user_joined(conn, r['id'])) for r in rows]


def site_public(row):
    return {
        'id': row['id'],
        'name': row['name'],
        'action': row['action'],
        'species': row['species'],
        'note': row['note'],
        'coords': [row['lng'], row['lat']],
        'valueRange': [row['value_min'], row['value_max']],
        'fundingGap': row['funding_gap'],
        'budget': row['budget'],
        'hectares': row['hectares'],
        'description': row['description'],
    }


def list_sites(conn):
    return [site_public(r) for r in conn.execute('SELECT * FROM sites').fetchall()]


def opp_public(row):
    return {
        'id': row['id'],
        'title': row['title'],
        'place': row['place'],
        'when': row['when_text'],
        'need': row['need'],
        'spots': row['spots'],
        'help': row['help'],
    }


def list_opportunities(conn):
    return [opp_public(r) for r in conn.execute('SELECT * FROM opportunities').fetchall()]


def partner_public(row):
    return {
        'id': row['id'],
        'name': row['name'],
        'type': row['type'],
        'place': row['place'],
        'focus': row['focus'],
        'people': row['people'],
    }


def list_partners(conn):
    return [partner_public(r) for r in conn.execute('SELECT * FROM organisations ORDER BY name').fetchall()]


def join_opportunity(conn, user_id, opportunity_id):
    result = _join_row(conn, user_id, opportunity_id, now_iso())
    conn.commit()
    return result


def leave_opportunity(conn, user_id, opportunity_id):
    opp = conn.execute('SELECT * FROM opportunities WHERE id = ?', (opportunity_id,)).fetchone()
    if not opp:
        raise KeyError('opportunity')
    existing = conn.execute(
        'SELECT 1 FROM signups WHERE user_id = ? AND opportunity_id = ?',
        (user_id, opportunity_id),
    ).fetchone()
    if not existing:
        return 'missing'
    conn.execute(
        'DELETE FROM signups WHERE user_id = ? AND opportunity_id = ?',
        (user_id, opportunity_id),
    )
    conn.execute(
        'UPDATE opportunities SET spots = spots + 1 WHERE id = ?',
        (opportunity_id,),
    )
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    _event(
        conn,
        icon='👋',
        tone='muted',
        title=f"{user['name']} left {opp['title']}",
        detail=opp['place'] or '',
        time=now_iso(),
        kind='leave',
        ref_id=opportunity_id,
    )
    conn.commit()
    return 'ok'


def report_public(row):
    return {
        'id': row['id'],
        'place': row['place'],
        'note': row['note'],
        'status': row['status'],
        'who': row['who'],
        'time': row['time'],
        'lng': row['lng'],
        'lat': row['lat'],
    }


def list_reports(conn):
    return [report_public(r) for r in conn.execute('SELECT * FROM reports ORDER BY time DESC').fetchall()]


def create_report(conn, *, place, note, status=None, who=None, lng=None, lat=None, user_id=None):
    status = status if status in REPORT_STATUSES else REPORT_STATUSES[0]
    if lng is None or lat is None:
        lng, lat = DEFAULT_PIN
    if not who and user_id:
        user = get_user(conn, user_id=user_id)
        who = user['name'] if user else who
    rid = new_id('r')
    when = now_iso()
    conn.execute(
        '''INSERT INTO reports (id, place, note, status, who, time, lng, lat, user_id)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        (rid, place, note, status, who, when, lng, lat, user_id),
    )
    _event(
        conn,
        icon='📍',
        tone='warn',
        title=f'Field report · {place}',
        detail=note or '',
        time=when,
        kind='report',
        ref_id=rid,
    )
    conn.commit()
    return report_public(conn.execute('SELECT * FROM reports WHERE id = ?', (rid,)).fetchone())


def patch_report(conn, report_id, status):
    if status not in REPORT_STATUSES:
        raise ValueError('status')
    row = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
    if not row:
        raise KeyError('report')
    conn.execute('UPDATE reports SET status = ? WHERE id = ?', (status, report_id))
    _event(
        conn,
        icon='✅' if status == 'Verified' else '📍',
        tone='good' if status == 'Verified' else 'info',
        title=f'Report {status.lower()}',
        detail=row['place'] or '',
        time=now_iso(),
        kind='report',
        ref_id=report_id,
    )
    conn.commit()
    return report_public(conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone())


def list_activity(conn, limit=50):
    rows = conn.execute(
        'SELECT * FROM activity_events ORDER BY time DESC, id DESC LIMIT ?',
        (limit,),
    ).fetchall()
    return [
        {
            'id': r['id'],
            'icon': r['icon'],
            'tone': r['tone'],
            'title': r['title'],
            'detail': r['detail'],
            'time': r['time'],
            'kind': r['kind'],
            'ref_id': r['ref_id'],
        }
        for r in rows
    ]


def project_public(row):
    return {
        'id': row['id'],
        'name': row['name'],
        'label': row['label'],
        'coords': [row['lng'], row['lat']],
    }


def list_projects(conn):
    return [project_public(r) for r in conn.execute('SELECT * FROM projects').fetchall()]


def create_project(conn, *, name, label=None, lng=None, lat=None):
    pid = new_id('p')
    conn.execute(
        'INSERT INTO projects (id, name, label, lng, lat) VALUES (?,?,?,?,?)',
        (pid, name, label, lng, lat),
    )
    conn.commit()
    return project_public(conn.execute('SELECT * FROM projects WHERE id = ?', (pid,)).fetchone())


def get_project(conn, project_id):
    return conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()


def scenario_public(row):
    return {
        'id': row['id'],
        'project_id': row['project_id'],
        'name': row['name'],
        'comparison': row['comparison'],
        'inputs': json.loads(row['inputs']),
        'results': json.loads(row['results']),
        'createdAt': row['created_at'],
    }


def list_scenarios(conn, project_id):
    rows = conn.execute(
        'SELECT * FROM scenarios WHERE project_id = ? ORDER BY created_at DESC',
        (project_id,),
    ).fetchall()
    return [scenario_public(r) for r in rows]


def create_scenario(conn, project_id, *, comparison, inputs, results, name=None):
    if comparison not in COMPARISONS:
        raise ValueError('comparison')
    sid = new_id('sc')
    when = now_iso()
    conn.execute(
        '''INSERT INTO scenarios (id, project_id, name, comparison, inputs, results, created_at)
           VALUES (?,?,?,?,?,?,?)''',
        (sid, project_id, name or comparison, comparison, json.dumps(inputs), json.dumps(results), when),
    )
    _event(
        conn,
        icon='📈',
        tone='info',
        title=f'Saved {comparison} scenario',
        detail=name or comparison,
        time=when,
        kind='scenario',
        ref_id=sid,
    )
    conn.commit()
    return scenario_public(conn.execute('SELECT * FROM scenarios WHERE id = ?', (sid,)).fetchone())


def draft_public(row):
    return {
        'id': row['id'],
        'site': row['site'],
        'type': row['type'],
        'createdAt': row['created_at'],
        'partner_id': row['partner_id'],
        'people_id': row['people_id'],
    }


def list_drafts(conn):
    return [draft_public(r) for r in conn.execute('SELECT * FROM response_drafts ORDER BY created_at DESC').fetchall()]


def create_draft(conn, *, site, type, partner_id=None, people_id=None):
    site_row = conn.execute('SELECT id FROM sites WHERE id = ?', (site,)).fetchone()
    if not site_row:
        raise KeyError('site')
    did = new_id('d')
    when = now_iso()
    conn.execute(
        '''INSERT INTO response_drafts (id, site, type, created_at, partner_id, people_id)
           VALUES (?,?,?,?,?,?)''',
        (did, site, type, when, partner_id, people_id),
    )
    conn.commit()
    return draft_public(conn.execute('SELECT * FROM response_drafts WHERE id = ?', (did,)).fetchone())


def lookups(conn):
    regions = [r['value'] for r in conn.execute("SELECT value FROM lookups WHERE kind = 'region'").fetchall()]
    help_options = [
        {'id': r['value'], 'label': r['label']}
        for r in conn.execute("SELECT value, label FROM lookups WHERE kind = 'help'").fetchall()
    ]
    return {'regions': regions, 'helpOptions': help_options}


def stats(conn):
    sites = list_sites(conn)
    drafts = list_drafts(conn)
    partners = list_partners(conn)
    people_users = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'people'").fetchone()[0]
    partner_people = sum(p['people'] or 0 for p in partners)
    hectares = sum((s['hectares'] or 0) for s in sites)
    funding = sum((s['budget'] or 0) for s in sites)
    gap = sum((s['fundingGap'] or 0) for s in sites)
    return {
        'interventions': {
            'sites': len(sites),
            'drafts': len(drafts),
        },
        'hectares': hectares or None,
        'funding_eur': funding or None,
        'funding_gap_eur': gap or None,
        'people': people_users + partner_people,
        'people_users': people_users,
        'people_partners': partner_people,
        'funding_split': None,
        'gaps': [
            'Overview tile 18/24 interventions is still a UI headline — DB has 3 seeded sites and draft count, not a 24-item programme list.',
            'Funding split 44/32/24 is still client-only; sites store budget and fundingGap but no public/EU/private share.',
        ],
    }
