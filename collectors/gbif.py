"""Shared GBIF helpers. CC0 / CC BY only (drop CC BY-NC)."""
import logging

import httpx

from collectors.region import USER_AGENT

logger = logging.getLogger(__name__)

GBIF_SEARCH = 'https://api.gbif.org/v1/occurrence/search'
GBIF_DATASET_SEARCH = 'https://api.gbif.org/v1/dataset/search'


def license_ok(lic: str):
    if not lic:
        return False, ''
    low = lic.lower().replace('_', '')
    if 'publicdomain/zero' in low or 'cc0' in low:
        return True, 'CC0'
    if 'creativecommons.org/licenses/by-nc' in low or 'cc-by-nc' in low or 'ccbync' in low:
        return False, ''
    if 'creativecommons.org/licenses/by' in low or low.startswith('ccby') or 'cc_by' in lic.lower():
        if 'nc' in low:
            return False, ''
        return True, 'CC_BY'
    return False, ''


def gbif_client():
    return httpx.Client(timeout=60, headers={'User-Agent': USER_AGENT})


def occurrence_page(client, params: dict) -> dict:
    resp = client.get(GBIF_SEARCH, params=params)
    if resp.status_code == 400:
        logger.warning('GBIF 400 for %s', params)
        return {'results': [], 'count': 0}
    resp.raise_for_status()
    return resp.json()
