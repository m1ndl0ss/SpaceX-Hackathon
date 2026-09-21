"""EEA Natura 2000 sites for NL, BE, LU (live polygons / bbox)."""
import logging

import httpx

from collectors.base import CollectedRecord, now_iso, with_retry
from collectors import overpass
from collectors.region import COUNTRIES, EAST, NORTH, SOUTH, USER_AGENT, WEST, OVERPASS_BBOX, in_bbox

logger = logging.getLogger(__name__)

SOURCE_ID = 'S001'
EEA_BASE = 'https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer'
EEA_LAYERS = (0, 1, 2)
EEA_URL = 'https://www.eea.europa.eu/en/datahub/datahubitem-view/6fc8ad2d-195d-40f4-bdec-576e7d1268e4'
MAX_SITES = 400


def _bbox_from_geom(geom: dict | None):
    if not geom:
        return None
    coords = geom.get('coordinates')
    if not coords:
        return None
    xs, ys = [], []

    def walk(node):
        if not isinstance(node, (list, tuple)) or not node:
            return
        if isinstance(node[0], (int, float)):
            xs.append(float(node[0]))
            ys.append(float(node[1]))
            return
        for child in node:
            walk(child)

    walk(coords)
    if not xs:
        return None
    return [min(xs), min(ys), max(xs), max(ys)]


def _box_poly(b):
    minx, miny, maxx, maxy = b
    ring = [[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]
    return {'type': 'Polygon', 'coordinates': [ring]}


def _geom_too_heavy(geom: dict | None, limit=80) -> bool:
    if not geom:
        return True
    coords = geom.get('coordinates')
    if not coords:
        return True
    n = 0

    def walk(node):
        nonlocal n
        if n > limit:
            return
        if not isinstance(node, (list, tuple)) or not node:
            return
        if isinstance(node[0], (int, float)):
            n += 1
            return
        for child in node:
            walk(child)

    walk(coords)
    return n > limit


def _record(site_id, name, kind, bbox, geometry, extra, live=True):
    geom = geometry
    if geom is None or _geom_too_heavy(geom):
        geom = _box_poly(bbox) if bbox else None
    raw = {
        'id': site_id,
        'sitecode': site_id,
        'name': name,
        'kind': kind,
        'bbox': bbox,
        **extra,
    }
    return CollectedRecord(
        source_id=SOURCE_ID,
        source_name='EEA Natura 2000' if live else 'Natura 2000 (OSM / clip)',
        source_url=EEA_URL,
        collected_at=now_iso(),
        license='EEA' if live else extra.get('license', 'ODbL'),
        geometry=geom,
        raw=raw,
    )


def _eea_query(client, layer: int, offset: int) -> dict:
    params = {
        'where': "MS IN ('NL','BE','LU')",
        'geometry': f'{WEST},{SOUTH},{EAST},{NORTH}',
        'geometryType': 'esriGeometryEnvelope',
        'inSR': 4326,
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'SITECODE,SITENAME,MS,SITETYPE,Area_km2,Area_ha',
        'returnGeometry': 'true',
        'outSR': 4326,
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': 200,
        'maxAllowableOffset': 0.01,
        'geometryPrecision': 4,
    }
    url = f'{EEA_BASE}/{layer}/query'
    resp = client.get(url, params=params, timeout=90)
    resp.raise_for_status()
    return resp.json()


def _from_eea():
    recs = []
    seen = set()
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
    with httpx.Client(timeout=90, headers=headers) as client:
        for layer in EEA_LAYERS:
            offset = 0
            while len(recs) < MAX_SITES and offset < 800:
                data = with_retry(lambda ly=layer, off=offset: _eea_query(client, ly, off))
                features = data.get('features') or []
                if not features:
                    break
                for feat in features:
                    props = feat.get('properties') or {}
                    sitecode = props.get('SITECODE')
                    ms = (props.get('MS') or '')[:2].upper()
                    if not sitecode or sitecode in seen or ms not in COUNTRIES:
                        continue
                    geom = feat.get('geometry')
                    bbox = _bbox_from_geom(geom)
                    if not bbox:
                        continue
                    cx = (bbox[0] + bbox[2]) / 2
                    cy = (bbox[1] + bbox[3]) / 2
                    if not in_bbox(cx, cy) and not (
                        bbox[0] <= EAST and bbox[2] >= WEST and bbox[1] <= NORTH and bbox[3] >= SOUTH
                    ):
                        continue
                    seen.add(sitecode)
                    recs.append(_record(
                        sitecode,
                        props.get('SITENAME') or sitecode,
                        props.get('SITETYPE') or 'natura2000',
                        bbox,
                        geom,
                        {
                            'ms': ms,
                            'area_km2': props.get('Area_km2'),
                            'area_ha': props.get('Area_ha'),
                            'layer': layer,
                            'source': 'EEA Natura 2000 2024 MapServer',
                        },
                        live=True,
                    ))
                    if len(recs) >= MAX_SITES:
                        break
                if len(features) < 200:
                    break
                offset += 200
            if len(recs) >= MAX_SITES:
                break
    logger.info('EEA Natura 2000 sites: %s', len(recs))
    return recs


def _from_osm():
    ql = f"""
[out:json][timeout:60];
(
  nwr["ref:EU:Natura2000"~"^(NL|BE|LU)"]({OVERPASS_BBOX});
  nwr["natura2000"~"^(NL|BE|LU)"]({OVERPASS_BBOX});
);
out tags bb 200;
"""
    data = overpass.query(ql)
    recs = []
    seen = set()
    for el in data.get('elements') or []:
        tags = el.get('tags') or {}
        sitecode = tags.get('ref:EU:Natura2000') or tags.get('natura2000') or tags.get('ref')
        if not sitecode or sitecode in seen:
            continue
        if sitecode[:2] not in COUNTRIES:
            continue
        bounds = el.get('bounds')
        if not bounds:
            continue
        bbox = [bounds['minlon'], bounds['minlat'], bounds['maxlon'], bounds['maxlat']]
        seen.add(sitecode)
        recs.append(_record(
            sitecode,
            tags.get('name') or sitecode,
            tags.get('protect_class') or 'natura2000',
            bbox,
            _box_poly(bbox),
            {'osm_id': el.get('id'), 'source': 'OSM Natura 2000 tags', 'license': 'ODbL'},
            live=False,
        ))
    return recs


def _fallback_clip():
    # Official sitecodes with approximate bboxes. Used only if live EEA/OSM fail.
    areas = [
        {'id': 'NL9801023', 'name': 'Veluwe', 'kind': 'SCI/SPA', 'bbox': [5.55, 52.00, 6.20, 52.45], 'ms': 'NL'},
        {'id': 'NL2000002', 'name': 'IJsselmeer', 'kind': 'SPA', 'bbox': [5.00, 52.40, 5.80, 53.00], 'ms': 'NL'},
        {'id': 'NL3009014', 'name': 'Biesbosch', 'kind': 'SCI/SPA', 'bbox': [4.65, 51.68, 4.95, 51.82], 'ms': 'NL'},
        {'id': 'NL2003055', 'name': 'Duinen Goeree & Kwade Hoek', 'kind': 'SCI', 'bbox': [3.85, 51.80, 4.10, 51.90], 'ms': 'NL'},
        {'id': 'NL9803031', 'name': 'Waddenzee', 'kind': 'SCI/SPA', 'bbox': [4.80, 52.90, 7.10, 53.55], 'ms': 'NL'},
        {'id': 'BE2100015', 'name': 'Kalmthoutse Heide', 'kind': 'SCI', 'bbox': [4.40, 51.38, 4.52, 51.45], 'ms': 'BE'},
        {'id': 'BE2300044', 'name': 'Schelde- en Durme-estuarium', 'kind': 'SCI', 'bbox': [4.00, 51.05, 4.40, 51.30], 'ms': 'BE'},
        {'id': 'BE33057C0', 'name': 'Hautes-Fagnes', 'kind': 'SCI', 'bbox': [6.00, 50.48, 6.20, 50.58], 'ms': 'BE'},
        {'id': 'BE34031C0', 'name': 'Vallée de la Semois', 'kind': 'SCI', 'bbox': [4.95, 49.78, 5.45, 49.92], 'ms': 'BE'},
        {'id': 'LU0001014', 'name': 'Vallée supérieure de la Sûre', 'kind': 'SCI', 'bbox': [5.75, 49.82, 6.00, 50.00], 'ms': 'LU'},
        {'id': 'LU0001011', 'name': "Vallée de la Mamer et de l'Eisch", 'kind': 'SCI', 'bbox': [5.95, 49.65, 6.15, 49.78], 'ms': 'LU'},
        {'id': 'LU0002002', 'name': "Vallée de l'Our", 'kind': 'SPA', 'bbox': [6.10, 49.90, 6.22, 50.14], 'ms': 'LU'},
    ]
    recs = []
    for a in areas:
        recs.append(_record(
            a['id'], a['name'], a['kind'], a['bbox'], _box_poly(a['bbox']),
            {'ms': a['ms'], 'source': 'Benelux Natura 2000 clip', 'license': 'fixture'},
            live=False,
        ))
        recs[-1].license = 'fixture'
        recs[-1].source_name = 'Natura 2000 Benelux clip (fixture)'
    return recs


def collect_all():
    try:
        recs = _from_eea()
        if recs:
            return recs
        logger.warning('EEA returned no sites; trying OSM')
    except Exception as e:
        logger.warning('EEA Natura 2000 failed: %s', e)
    try:
        recs = _from_osm()
        if recs:
            return recs
    except Exception as e:
        logger.warning('OSM Natura 2000 failed: %s', e)
    logger.warning('using Natura 2000 Benelux clip fixture')
    return _fallback_clip()
