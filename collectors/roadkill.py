"""Wildlife-vehicle collisions: Grilo 2025 Global Roadkill Data via GBIF."""
import logging

from collectors.base import CollectedRecord, now_iso, with_retry
from collectors.gbif import gbif_client, license_ok, occurrence_page
from collectors.region import COUNTRIES, GBIF_BBOX, in_bbox

logger = logging.getLogger(__name__)

SOURCE_ID = 'C006'
# Grilo et al. 2025 Scientific Data — Global Roadkill Data on GBIF
DATASETS = [
    {
        'key': '65908f95-5ab6-48d9-bf6d-6da274ed730e',
        'name': 'Global Roadkill Data (opportunistic)',
    },
    {
        'key': 'd3b6cb30-0a64-4f82-91ea-0bb14637ee17',
        'name': 'Global Roadkill Data (systematic)',
    },
]
SPECIES = [
    {'slug': 'meles_meles', 'name': 'Meles meles', 'taxon_key': 5219243},
    {'slug': 'cervus_elaphus', 'name': 'Cervus elaphus', 'taxon_key': 2440954},
    {'slug': 'capreolus_capreolus', 'name': 'Capreolus capreolus', 'taxon_key': 2440946},
    {'slug': 'sus_scrofa', 'name': 'Sus scrofa', 'taxon_key': 2704179},
    {'slug': 'castor_fiber', 'name': 'Castor fiber', 'taxon_key': 2432164},
]
PER_QUERY_CAP = 200
PAGE_SIZE = 200


def _append(records, seen, occ, sp, dataset_name, license_id):
    key = occ.get('key')
    lon = occ.get('decimalLongitude')
    lat = occ.get('decimalLatitude')
    if key in seen or not in_bbox(lon, lat):
        return False
    country = occ.get('countryCode')
    if country and country not in COUNTRIES:
        return False
    seen.add(key)
    records.append(CollectedRecord(
        source_id=SOURCE_ID,
        source_name='GBIF Global Roadkill Data (Grilo 2025)',
        source_url=f'https://www.gbif.org/occurrence/{key}',
        collected_at=now_iso(),
        license=license_id,
        geometry={'type': 'Point', 'coordinates': [lon, lat]},
        raw={
            'species_slug': sp['slug'],
            'scientificName': occ.get('scientificName') or sp['name'],
            'species': occ.get('scientificName') or sp['name'],
            'taxonKey': sp['taxon_key'],
            'gbifId': key,
            'lng': lon,
            'lat': lat,
            'year': occ.get('year'),
            'license': license_id,
            'country': country,
            'datasetName': occ.get('datasetName') or dataset_name,
            'datasetKey': occ.get('datasetKey'),
        },
    ))
    return True


def collect_all():
    records = []
    seen = set()
    with gbif_client() as client:
        for ds in DATASETS:
            for sp in SPECIES:
                for country in COUNTRIES:
                    offset = 0
                    kept = 0
                    while kept < PER_QUERY_CAP and offset < PER_QUERY_CAP:
                        params = {
                            'datasetKey': ds['key'],
                            'taxonKey': sp['taxon_key'],
                            'country': country,
                            'hasCoordinate': 'true',
                            'limit': PAGE_SIZE,
                            'offset': offset,
                            **GBIF_BBOX,
                        }
                        data = with_retry(lambda p=params: occurrence_page(client, p))
                        results = data.get('results') or []
                        if not results:
                            break
                        for occ in results:
                            ok, license_id = license_ok(occ.get('license') or '')
                            if not ok:
                                # Grilo datasets are CC BY; keep labeled records if license missing
                                lic = occ.get('license') or ''
                                if lic:
                                    continue
                                license_id = 'CC_BY'
                            if _append(records, seen, occ, sp, ds['name'], license_id):
                                kept += 1
                        if offset + len(results) >= data.get('count', 0):
                            break
                        offset += PAGE_SIZE
                    if kept:
                        logger.info('roadkill %s %s %s: %s', ds['name'][:22], sp['slug'], country, kept)

        if len(records) < 20:
            logger.info('few Grilo hits; searching GBIF q=roadkill in Benelux')
            for sp in SPECIES:
                for country in COUNTRIES:
                    params = {
                        'taxonKey': sp['taxon_key'],
                        'country': country,
                        'hasCoordinate': 'true',
                        'q': 'roadkill',
                        'limit': PAGE_SIZE,
                        **GBIF_BBOX,
                    }
                    data = with_retry(lambda p=params: occurrence_page(client, p))
                    for occ in data.get('results') or []:
                        ok, license_id = license_ok(occ.get('license') or '')
                        if not ok:
                            continue
                        _append(records, seen, occ, sp, 'GBIF q=roadkill', license_id)
    logger.info('roadkill records: %s', len(records))
    return records
