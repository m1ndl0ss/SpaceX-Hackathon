from __future__ import annotations

import json

from impact_models import paths
from impact_models.features import data_flags, feature_row, hit_sites
from impact_models.schema import Treatment
from impact_models.warehouse import clear_warehouse_cache


def test_missing_warehouse_zeros(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", tmp_path / "raw")
    clear_warehouse_cache()
    row = feature_row(Treatment(typeId="wind", center=(5.6874, 50.8218)), include_observations=True)
    assert row["gbif_suitability"] == 0.0
    assert row["roadkill_intensity_2km"] == 0.0
    assert row["min_road_km"] == 25.0


def test_warehouse_points_and_roads(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "gbif_latest.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "C001",
                    "source_name": "GBIF",
                    "source_url": "https://example.local/occ",
                    "collected_at": "2026-01-01T00:00:00+00:00",
                    "license": "CC0_1_0",
                    "geometry": {"type": "Point", "coordinates": [5.6874, 50.8218]},
                    "raw": {"scientificName": "Myotis myotis"},
                }
            ]
        ),
        encoding="utf-8",
    )
    (raw / "osm_roads_latest.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "S005",
                    "source_name": "OSM",
                    "source_url": "https://www.openstreetmap.org/copyright",
                    "collected_at": "2026-01-01T00:00:00+00:00",
                    "license": "ODbL",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[5.6870, 50.8215], [5.6880, 50.8220]],
                    },
                    "raw": {},
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", raw)
    clear_warehouse_cache()
    row = feature_row(Treatment(typeId="wind", center=(5.6874, 50.8218)), include_observations=True)
    assert row["gbif_suitability"] > 0
    assert row["min_road_km"] < 1.0
    flags = data_flags()
    assert flags["gbif"] is True
    assert flags["osm_roads"] is True
    clear_warehouse_cache()


def test_warehouse_replaces_curated_and_weather(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "protected_areas_latest.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "S001",
                    "source_name": "Natura",
                    "source_url": "https://example.local/pa",
                    "collected_at": "2026-01-01T00:00:00+00:00",
                    "license": "CC0",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[5.84, 52.14], [5.86, 52.14], [5.86, 52.16], [5.84, 52.16], [5.84, 52.14]]],
                    },
                    "raw": {"id": "warehouse-park", "name": "Warehouse park", "species": ["Red deer"]},
                }
            ]
        ),
        encoding="utf-8",
    )
    (raw / "water_latest.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "S002",
                    "source_name": "Water",
                    "source_url": "https://example.local/water",
                    "collected_at": "2026-01-01T00:00:00+00:00",
                    "license": "CC0",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[5.84, 52.14], [5.86, 52.14], [5.86, 52.16], [5.84, 52.16], [5.84, 52.14]]],
                    },
                    "raw": {"id": "warehouse-water", "name": "Warehouse water"},
                }
            ]
        ),
        encoding="utf-8",
    )
    (raw / "open_meteo_latest.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "S004",
                    "source_name": "Open-Meteo",
                    "source_url": "https://open-meteo.com/",
                    "collected_at": "2026-01-01T00:00:00+00:00",
                    "license": "CC BY 4.0",
                    "geometry": {"type": "Point", "coordinates": [5.85, 52.15]},
                    "raw": {
                        "daily": {
                            "snowfall_sum": [2.0, 4.0],
                            "precipitation_sum": [10.0, 14.0],
                            "wind_speed_10m_max": [5.0, 7.0],
                        }
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", raw)
    clear_warehouse_cache()
    pin = (5.85, 52.15)
    sites = hit_sites(pin, "wind")
    ids = {site.id for site in sites}
    assert "warehouse-park" in ids
    assert "warehouse-water" in ids
    assert "sint-pietersberg" not in ids
    row = feature_row(Treatment(typeId="wind", center=pin), include_observations=False)
    assert row["snow_mm"] == 3.0
    assert row["precip_mm"] == 12.0
    assert row["water_overlap"] == 1.0
    clear_warehouse_cache()


def test_warehouse_clips_outside_bbox(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "gbif_latest.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "C001",
                    "source_name": "GBIF",
                    "source_url": "https://example.local/occ",
                    "collected_at": "2026-01-01T00:00:00+00:00",
                    "license": "CC0_1_0",
                    "geometry": {"type": "Point", "coordinates": [13.78, 41.81]},
                    "raw": {"scientificName": "Myotis myotis"},
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", raw)
    clear_warehouse_cache()
    row = feature_row(Treatment(typeId="wind", center=(5.6874, 50.8218)), include_observations=True)
    assert row["gbif_suitability"] == 0.0
    clear_warehouse_cache()
