"""Open-Meteo monthly climatology at Benelux centroids. No API key."""
import logging
from collections import defaultdict

import httpx

from collectors.base import CollectedRecord, now_iso, with_retry
from collectors.region import USER_AGENT

logger = logging.getLogger(__name__)

SOURCE_ID = 'S004'
ARCHIVE = 'https://archive-api.open-meteo.com/v1/archive'
SITES = [
    {'id': 'maastricht', 'lat': 50.8514, 'lon': 5.6900, 'name': 'Maastricht'},
    {'id': 'antwerp', 'lat': 51.2194, 'lon': 4.4025, 'name': 'Antwerp'},
    {'id': 'luxembourg', 'lat': 49.6116, 'lon': 6.1319, 'name': 'Luxembourg'},
    {'id': 'veluwe', 'lat': 52.2340, 'lon': 5.8920, 'name': 'Veluwe'},
    {'id': 'ardennes', 'lat': 50.1830, 'lon': 5.5750, 'name': 'Ardennes'},
]
DAILY = 'temperature_2m_mean,precipitation_sum,snowfall_sum,wind_speed_10m_max'


def _monthly_from_daily(daily: dict) -> dict:
    buckets = defaultdict(lambda: {'temp': [], 'precip': 0.0, 'snow': 0.0, 'wind': []})
    times = daily.get('time') or []
    temps = daily.get('temperature_2m_mean') or []
    precips = daily.get('precipitation_sum') or []
    snows = daily.get('snowfall_sum') or []
    winds = daily.get('wind_speed_10m_mean') or daily.get('wind_speed_10m_max') or []
    for i, t in enumerate(times):
        month = t[:7]
        b = buckets[month]
        if i < len(temps) and temps[i] is not None:
            b['temp'].append(temps[i])
        if i < len(precips) and precips[i] is not None:
            b['precip'] += precips[i]
        if i < len(snows) and snows[i] is not None:
            b['snow'] += snows[i]
        if i < len(winds) and winds[i] is not None:
            b['wind'].append(winds[i])
    months = sorted(buckets)
    return {
        'time': months,
        'temperature_2m_mean': [
            (round(sum(buckets[m]['temp']) / len(buckets[m]['temp']), 2) if buckets[m]['temp'] else None)
            for m in months
        ],
        'precipitation_sum': [round(buckets[m]['precip'], 2) for m in months],
        'snowfall_sum': [round(buckets[m]['snow'], 2) for m in months],
        'wind_speed_10m_mean': [
            (round(sum(buckets[m]['wind']) / len(buckets[m]['wind']), 2) if buckets[m]['wind'] else None)
            for m in months
        ],
    }


def collect_all():
    records = []
    headers = {'User-Agent': USER_AGENT}
    with httpx.Client(timeout=60, headers=headers) as client:
        for site in SITES:
            params = {
                'latitude': site['lat'],
                'longitude': site['lon'],
                'start_date': '2015-01-01',
                'end_date': '2024-12-31',
                'daily': DAILY,
                'timezone': 'Europe/Brussels',
            }
            resp = with_retry(lambda p=params: client.get(ARCHIVE, params=p))
            resp.raise_for_status()
            data = resp.json()
            monthly = _monthly_from_daily(data.get('daily') or {})
            records.append(CollectedRecord(
                source_id=SOURCE_ID,
                source_name='Open-Meteo archive (monthly climatology)',
                source_url='https://open-meteo.com/',
                collected_at=now_iso(),
                license='CC BY 4.0',
                geometry={'type': 'Point', 'coordinates': [site['lon'], site['lat']]},
                raw={
                    'site': site,
                    'lng': site['lon'],
                    'lat': site['lat'],
                    'period': '2015-01 to 2024-12 monthly means from Open-Meteo ERA5 daily archive',
                    'monthly': monthly,
                },
            ))
    logger.info('Open-Meteo sites: %s', len(records))
    return records
