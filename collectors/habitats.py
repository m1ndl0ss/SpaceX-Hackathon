"""GBIF occurrences for Benelux habitat species (CC0 / CC BY only)."""
import logging

from collectors.base import CollectedRecord, now_iso, with_retry
from collectors.gbif import gbif_client, license_ok, occurrence_page
from collectors.region import COUNTRIES, GBIF_BBOX, in_bbox

logger = logging.getLogger(__name__)

SOURCE_ID = 'C001'
PER_SPECIES_CAP = 200
PAGE_SIZE = 200

SPECIES = [
    {'slug': 'myotis_myotis', 'name': 'Myotis myotis', 'taxon_key': 2432384},
    {'slug': 'meles_meles', 'name': 'Meles meles', 'taxon_key': 5219243},
    {'slug': 'castor_fiber', 'name': 'Castor fiber', 'taxon_key': 2432164},
    {'slug': 'alcedo_atthis', 'name': 'Alcedo atthis', 'taxon_key': 2475479},
    {'slug': 'bombina_variegata', 'name': 'Bombina variegata', 'taxon_key': 2426614},
    {'slug': 'alauda_arvensis', 'name': 'Alauda arvensis', 'taxon_key': 2490742},
    {'slug': 'podiceps_cristatus', 'name': 'Podiceps cristatus', 'taxon_key': 2482142},
    {'slug': 'acrocephalus_scirpaceus', 'name': 'Acrocephalus scirpaceus', 'taxon_key': 2493754},
    {'slug': 'lutra_lutra', 'name': 'Lutra lutra', 'taxon_key': 2435091},
    {'slug': 'ciconia_ciconia', 'name': 'Ciconia ciconia', 'taxon_key': 2480637},
    {'slug': 'cervus_elaphus', 'name': 'Cervus elaphus', 'taxon_key': 2440954},
]


def collect_all():
    records = []
    seen = set()
    with gbif_client() as client:
        for sp in SPECIES:
            kept = 0
            for country in COUNTRIES:
                for license_filter in ('CC0_1_0', 'CC_BY_4_0'):
                    if kept >= PER_SPECIES_CAP:
                        break
                    offset = 0
                    while kept < PER_SPECIES_CAP and offset < 400:
                        params = {
                            'taxonKey': sp['taxon_key'],
                            'country': country,
                            'hasCoordinate': 'true',
                            'license': license_filter,
                            'limit': PAGE_SIZE,
                            'offset': offset,
                            **GBIF_BBOX,
                        }
                        data = with_retry(lambda p=params: occurrence_page(client, p))
                        results = data.get('results') or []
                        if not results:
                            break
                        for occ in results:
                            if kept >= PER_SPECIES_CAP:
                                break
                            ok, license_id = license_ok(occ.get('license') or '')
                            if not ok:
                                continue
                            key = occ.get('key')
                            lon = occ.get('decimalLongitude')
                            lat = occ.get('decimalLatitude')
                            if key in seen or not in_bbox(lon, lat):
                                continue
                            country_code = occ.get('countryCode') or country
                            if country_code not in COUNTRIES:
                                continue
                            seen.add(key)
                            kept += 1
                            records.append(CollectedRecord(
                                source_id=SOURCE_ID,
                                source_name='GBIF',
                                source_url=f'https://www.gbif.org/occurrence/{key}',
                                collected_at=now_iso(),
                                license=license_id,
                                geometry={'type': 'Point', 'coordinates': [lon, lat]},
                                raw={
                                    'species_slug': sp['slug'],
                                    'scientificName': occ.get('scientificName') or sp['name'],
                                    'taxonKey': sp['taxon_key'],
                                    'gbifId': key,
                                    'lng': lon,
                                    'lat': lat,
                                    'year': occ.get('year'),
                                    'license': license_id,
                                    'country': country_code,
                                    'eventDate': occ.get('eventDate'),
                                    'basisOfRecord': occ.get('basisOfRecord'),
                                },
                            ))
                        if offset + len(results) >= data.get('count', 0):
                            break
                        offset += PAGE_SIZE
            logger.info('GBIF %s kept: %s', sp['slug'], kept)
    return records
