from __future__ import annotations

import numpy as np

from impact_models.features import feature_row
from impact_models.generate import HEADS, generate_frame, physical_labels, recipe_labels
from impact_models.schema import NearbyTreatment, Treatment


def test_generate_has_three_countries():
    frame = generate_frame(n=90, seed=2, include_observations=False)
    assert len(frame) == 90
    assert set(frame["country_idx"].unique()) >= {0.0, 1.0, 2.0}
    for head in HEADS:
        assert frame[head].notna().all()
        if head != "tco2e":
            assert (frame[head] >= -1e-9).all()
    assert frame["horizon_year"].min() >= 2026
    assert frame["horizon_year"].max() <= 2040
    assert (frame["scale"] >= 0.4).all()
    assert (frame["scale"] <= 2.0).all()


def test_generate_covers_2040_and_neighbors():
    frame = generate_frame(n=240, seed=4, include_observations=False)
    assert 2040 in set(frame["horizon_year"].astype(int))
    assert frame["nearby_2km"].max() > 0
    assert frame["nearby_highway_2km"].max() > 0


def test_highway_scales_with_road_proximity():
    rng = np.random.default_rng(1)
    far = feature_row(Treatment(typeId="highway", center=(5.85, 52.15)), include_observations=False)
    far["min_road_km"] = 8.0
    far["roadkill_intensity_2km"] = 0.0
    far["has_osm_roads"] = 1.0
    close = dict(far)
    close["min_road_km"] = 0.4
    close["roadkill_intensity_2km"] = 2.0
    close["has_osm_roads"] = 1.0
    rng = np.random.default_rng(1)
    far_y = physical_labels(far, rng)
    rng = np.random.default_rng(1)
    close_y = physical_labels(close, rng)
    assert close_y["habitatHa"] > far_y["habitatHa"]


def test_cooling_lowers_river_temp_recipe():
    rng = np.random.default_rng(0)
    base = Treatment(typeId="datacentre", center=(5.696, 50.851), horizonYear=2030, cooling=False)
    cool = Treatment(typeId="datacentre", center=(5.696, 50.851), horizonYear=2030, cooling=True)
    off = physical_labels(feature_row(base, include_observations=False), rng)
    rng = np.random.default_rng(0)
    on = physical_labels(feature_row(cool, include_observations=False), rng)
    assert on["riverTempC"] <= off["riverTempC"]


def test_buffer_lowers_habitat_recipe():
    rng = np.random.default_rng(0)
    base = Treatment(typeId="highway", center=(5.6874, 50.8218), buffer=False)
    buffered = Treatment(typeId="highway", center=(5.6874, 50.8218), buffer=True)
    off = physical_labels(feature_row(base, include_observations=False), rng)
    rng = np.random.default_rng(0)
    on = physical_labels(feature_row(buffered, include_observations=False), rng)
    assert on["habitatHa"] <= off["habitatHa"]


def test_neighbors_raise_cumulative_impact():
    pin = (5.85, 52.15)
    none = feature_row(Treatment(typeId="wind", center=pin), include_observations=False)
    busy = feature_row(
        Treatment(
            typeId="wind",
            center=pin,
            nearbyTreatments=[
                NearbyTreatment(typeId="highway", center=(5.852, 52.151)),
                NearbyTreatment(typeId="industrial", center=(5.849, 52.149)),
            ],
        ),
        include_observations=False,
    )
    assert busy["nearby_2km"] > none["nearby_2km"]
    off = recipe_labels(none)
    on = recipe_labels(busy)
    assert on["habitatHa"] > off["habitatHa"]
    assert on["riverTempC"] >= off["riverTempC"]
    assert on["energyIdx"] >= off["energyIdx"]


def test_weather_lowers_veg_and_river_when_available():
    row = feature_row(Treatment(typeId="solar", center=(5.85, 52.15)), include_observations=False)
    dry = dict(row)
    dry["has_open_meteo"] = 1.0
    dry["precip_mm"] = 20.0
    dry["snow_mm"] = 0.0
    wet = dict(dry)
    wet["precip_mm"] = 90.0
    wet["snow_mm"] = 8.0
    missing = dict(dry)
    missing["has_open_meteo"] = 0.0
    missing["precip_mm"] = 0.0
    missing["snow_mm"] = 0.0
    dry_y = recipe_labels(dry)
    wet_y = recipe_labels(wet)
    missing_y = recipe_labels(missing)
    assert wet_y["vegStress"] < dry_y["vegStress"]
    assert wet_y["riverTempC"] <= dry_y["riverTempC"]
    assert missing_y["vegStress"] == recipe_labels({**missing, "precip_mm": 90.0, "snow_mm": 8.0})["vegStress"]
