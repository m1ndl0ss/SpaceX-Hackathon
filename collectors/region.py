# Benelux demo window: Netherlands, Belgium, Luxembourg only.
# Bbox is west, south, east, north.
WEST, SOUTH, EAST, NORTH = 2.3, 49.4, 7.3, 53.7
COUNTRIES = ('NL', 'BE', 'LU')
# Overpass uses south, west, north, east
OVERPASS_BBOX = f'{SOUTH},{WEST},{NORTH},{EAST}'
GBIF_BBOX = {
    'decimalLongitude': f'{WEST},{EAST}',
    'decimalLatitude': f'{SOUTH},{NORTH}',
}
USER_AGENT = 'spacexhackathon-benelux-wildlife/0.2 (hackathon; cache collectors)'


def in_bbox(lon, lat) -> bool:
    if lon is None or lat is None:
        return False
    return WEST <= float(lon) <= EAST and SOUTH <= float(lat) <= NORTH
