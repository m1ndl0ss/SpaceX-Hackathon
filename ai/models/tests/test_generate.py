from __future__ import annotations

import numpy as np

from impact_models.features import feature_row
from impact_models.generate import HEADS, generate_frame, physical_labels
from impact_models.schema import Treatment


def test_generate_has_three_countries():
    frame = generate_frame(n=90, seed=2, include_observations=False)
    assert len(frame) == 90
    assert set(frame["country_idx"].unique()) >= {0.0, 1.0, 2.0}
    for head in HEADS:
        assert frame[head].notna().all()


def test_highway_scales_with_road_proximity():
    rng = np.random.default_rng(1)
    far = feature_row(Treatment(typeId="highway", center=(5.85, 52.15)), include_observations=False)
    far["min_road_km"] = 8.0
    far["roadkill_intensity_2km"] = 0.0
    close = dict(far)
    close["min_road_km"] = 0.4
    close["roadkill_intensity_2km"] = 2.0
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
