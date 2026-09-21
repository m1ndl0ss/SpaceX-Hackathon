"""Open-Meteo daily weather at a few Abruzzo centroids. No API key."""
import logging

import httpx

from collectors.base import CollectedRecord, now_iso, with_retry

logger = logging.getLogger(__name__)

SOURCE_ID = 'S004'
URL = 'https://api.open-meteo.com/v1/forecast'
SITES = [
    {'id': 'abruzzo_np', 'lat': 41.81, 'lon': 13.78, 'name': 'Parco Nazionale d\'Abruzzo'},
    {'id': 'maiella', 'lat': 42.09, 'lon': 14.11, 'name': 'Maiella'},
    {'id': 'sirente', 'lat': 42.16, 'lon': 13.58, 'name': 'Sirente-Velino'},
]


def collect_all():
    records = []
    with httpx.Client(timeout=30) as client:
        for site in SITES:
            params = {
                'latitude': site['lat'],
                'longitude': site['lon'],
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,wind_speed_10m_max',
                'timezone': 'Europe/Rome',
                'forecast_days': 7,
            }
            resp = with_retry(lambda p=params: client.get(URL, params=p))
            resp.raise_for_status()
            data = resp.json()
            records.append(CollectedRecord(
                source_id=SOURCE_ID,
                source_name='Open-Meteo',
                source_url='https://open-meteo.com/',
                collected_at=now_iso(),
                license='CC BY 4.0',
                geometry={'type': 'Point', 'coordinates': [site['lon'], site['lat']]},
                raw={'site': site, 'daily': data.get('daily', {})},
            ))
    logger.info('Open-Meteo sites: %s', len(records))
    return records
