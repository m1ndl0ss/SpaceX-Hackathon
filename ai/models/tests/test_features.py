from __future__ import annotations

from impact_models import paths
from impact_models.context import country_for_point
from impact_models.features import FEATURE_COLUMNS, feature_row, hit_sites
from impact_models.schema import Treatment
from impact_models.warehouse import clear_warehouse_cache


def test_feature_columns_are_portable():
    joined = " ".join(FEATURE_COLUMNS)
    assert "lng" not in FEATURE_COLUMNS
    assert "lat" not in FEATURE_COLUMNS
    assert "dist_sint-pietersberg_m" not in FEATURE_COLUMNS
    assert "country_idx" in FEATURE_COLUMNS
    assert "min_road_km" in FEATURE_COLUMNS
    assert "has_gbif" in FEATURE_COLUMNS
    assert "has_open_meteo" in FEATURE_COLUMNS
    assert "sint-pietersberg" not in joined


def test_sint_pietersberg_hits_habitat(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", tmp_path / "empty-raw")
    clear_warehouse_cache()
    treatment = Treatment(typeId="wind", center=(5.6874, 50.8218), horizonYear=2030)
    sites = hit_sites(treatment.center, treatment.typeId)
    names = {site.id for site in sites}
    assert "sint-pietersberg" in names
    clear_warehouse_cache()


def test_ardennes_closer_than_maastricht_water(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", tmp_path / "empty-raw")
    clear_warehouse_cache()
    fagnes = Treatment(typeId="wind", center=(6.13, 50.52), horizonYear=2030)
    maas = Treatment(typeId="datacentre", center=(5.696, 50.851), horizonYear=2030)
    fagnes_row = feature_row(fagnes, include_observations=False)
    maas_row = feature_row(maas, include_observations=False)
    assert fagnes_row["min_habitat_m"] < 8000
    assert maas_row["water_overlap"] == 1.0
    assert {site.id for site in hit_sites(fagnes.center, fagnes.typeId)} & {"hautes-fagnes"}
    clear_warehouse_cache()


def test_country_index_varies():
    nl = feature_row(Treatment(typeId="wind", center=(5.85, 52.15)), include_observations=False)
    be = feature_row(Treatment(typeId="wind", center=(4.35, 50.50)), include_observations=False)
    lu = feature_row(Treatment(typeId="wind", center=(6.13, 49.61)), include_observations=False)
    assert {nl["country_idx"], be["country_idx"], lu["country_idx"]} == {0.0, 1.0, 2.0}


def test_country_overlap_and_gap():
    assert country_for_point((6.13, 49.61)) == "LU"
    assert country_for_point((6.13, 49.80)) == "LU"
    assert country_for_point((6.5, 50.5)) == "BE"
