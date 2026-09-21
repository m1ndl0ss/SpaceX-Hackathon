"""GBIF occurrence collector for Ursus arctos (taxonKey 2433433).

Italy + Abruzzo bbox. License filter CC0 / CC BY only (drop CC BY-NC).
"""
import logging

import httpx

from collectors.base import CollectedRecord, now_iso, with_retry

logger = logging.getLogger(__name__)

SOURCE_ID = 'C001'
TAXON_KEY = 2433433
ALLOWED_LICENSES = {'CC0_1_0', 'CC_BY_4_0', 'CC_BY_3_0'}
# Abruzzo / central Apennines
BBOX = {'decimalLongitude': '13.0,14.5', 'decimalLatitude': '41.4,42.8'}
GBIF_SEARCH = 'https://api.gbif.org/v1/occurrence/search'


def _page(client, offset, extra):
    params = {
        'taxonKey': TAXON_KEY,
        'country': 'IT',
        'hasCoordinate': 'true',
        'limit': 300,
        'offset': offset,
        **extra,
    }
    resp = with_retry(lambda: client.get(GBIF_SEARCH, params=params))
    resp.raise_for_status()
    return resp.json()


def collect_all():
    logger.info('fetching GBIF Ursus arctos IT')
    records = []
    seen = set()

    with httpx.Client(timeout=60, headers={'User-Agent': 'spacexhackathon-bear-tracker/0.1'}) as client:
        for extra in ({}, BBOX):
            offset = 0
            while offset < 900:
                data = _page(client, offset, extra)
                results = data.get('results', [])
                if not results:
                    break
                for occ in results:
                    license_id = (occ.get('license') or '').split('/')[-1].replace('-', '_').upper()
                    # GBIF uses URIs like http://creativecommons.org/publicdomain/zero/1.0/
                    lic = occ.get('license') or ''
                    ok = False
                    if 'publicdomain/zero' in lic or license_id in ('CC0_1_0', 'CC0'):
                        ok = True
                        license_id = 'CC0_1_0'
                    elif 'creativecommons.org/licenses/by/' in lic:
                        ok = True
                        license_id = 'CC_BY'
                    if not ok:
                        continue
                    key = occ.get('key')
                    if key in seen:
                        continue
                    lon = occ.get('decimalLongitude')
                    lat = occ.get('decimalLatitude')
                    if lon is None or lat is None:
                        continue
                    seen.add(key)
                    records.append(CollectedRecord(
                        source_id=SOURCE_ID,
                        source_name='GBIF',
                        source_url=f'https://www.gbif.org/occurrence/{key}',
                        collected_at=now_iso(),
                        license=license_id,
                        geometry={'type': 'Point', 'coordinates': [lon, lat]},
                        raw={
                            'gbifId': key,
                            'eventDate': occ.get('eventDate'),
                            'year': occ.get('year'),
                            'locality': occ.get('locality'),
                            'basisOfRecord': occ.get('basisOfRecord'),
                            'datasetName': occ.get('datasetName'),
                            'scientificName': occ.get('scientificName'),
                            'decimalLongitude': lon,
                            'decimalLatitude': lat,
                        },
                    ))
                if offset + len(results) >= data.get('count', 0):
                    break
                offset += 300

    logger.info('GBIF records kept: %s', len(records))
    return records
