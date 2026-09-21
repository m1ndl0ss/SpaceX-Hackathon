import logging
import time

import httpx

from collectors.region import USER_AGENT

logger = logging.getLogger(__name__)

ENDPOINTS = [
    'https://overpass.openstreetmap.fr/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.private.coffee/api/interpreter',
    'https://overpass-api.de/api/interpreter',
]
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'application/json',
}


def query(ql: str) -> dict:
    last = None
    for url in ENDPOINTS:
        try:
            with httpx.Client(timeout=25, headers=HEADERS) as client:
                resp = client.post(url, data={'data': ql})
                if resp.status_code in (429, 502, 503, 504):
                    logger.warning('Overpass %s status %s', url, resp.status_code)
                    last = RuntimeError(f'{url} HTTP {resp.status_code}')
                    time.sleep(2)
                    continue
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            last = e
            logger.warning('Overpass %s failed: %s', url, e)
            time.sleep(1)
    raise last


def point(el: dict):
    if 'lat' in el and 'lon' in el:
        return el['lon'], el['lat']
    center = el.get('center')
    if center and 'lat' in center:
        return center['lon'], center['lat']
    geom = el.get('geometry') or []
    if geom:
        return geom[0]['lon'], geom[0]['lat']
    bounds = el.get('bounds')
    if bounds:
        lon = (bounds['minlon'] + bounds['maxlon']) / 2
        lat = (bounds['minlat'] + bounds['maxlat']) / 2
        return lon, lat
    return None
