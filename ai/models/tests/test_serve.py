from __future__ import annotations

from fastapi.testclient import TestClient

from impact_models import paths
from impact_models.infer import infer, load_boosters, load_cart, load_cart_text
from impact_models.schema import NearbyTreatment, Treatment
from impact_models.serve import app
from impact_models.train import train
from impact_models.warehouse import clear_warehouse_cache


def _train_isolated(tmp_path, monkeypatch, n: int = 360, seed: int = 3, rounds: int = 25):
    monkeypatch.setattr(paths, "ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr(paths, "BOOSTERS_DIR", tmp_path / "boosters")
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", tmp_path / "empty-raw")
    clear_warehouse_cache()
    load_boosters.cache_clear()
    load_cart.cache_clear()
    load_cart_text.cache_clear()
    metrics = train(n=n, seed=seed, rounds=rounds)
    load_boosters.cache_clear()
    load_cart.cache_clear()
    load_cart_text.cache_clear()
    return metrics


def test_train_infer_http(tmp_path, monkeypatch):
    metrics = _train_isolated(tmp_path, monkeypatch)
    assert "habitatHa" in metrics["heads"]
    assert "pinball" in metrics["heads"]["habitatHa"]["p50"]
    assert "coverage80" in metrics["heads"]["habitatHa"]
    assert "crossingBeforeSort" in metrics["heads"]["habitatHa"]
    assert "cartVsBoosterMae" in metrics

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    wind = client.post(
        "/infer",
        json={"typeId": "wind", "center": [5.6874, 50.8218], "horizonYear": 2040, "scale": 0.4},
    )
    assert wind.status_code == 200
    body = wind.json()
    assert body["country"] in {"NL", "BE", "LU"}
    assert body["outcomes"]["habitatHa"]["p10"] <= body["outcomes"]["habitatHa"]["p90"]
    assert body["outcomes"]["habitatHa"]["p10"] >= 0
    assert body["labelKind"] == "synthetic_scenario"
    assert body["shapTarget"] == "habitatHa"
    assert body["netMethod"] == "equal_mean_of_eight_sectors"
    assert body["scenarioEstimate"]["habitatHa"] >= 0
    assert " -> " in body["explainer"] or "leaf" in body["explainer"]
    field = client.post(
        "/infer",
        json={"typeId": "wind", "center": [5.29, 52.13], "horizonYear": 2030},
    )
    assert field.status_code == 200
    bad_scale = client.post(
        "/infer",
        json={"typeId": "wind", "center": [5.29, 52.13], "scale": 3.5},
    )
    assert bad_scale.status_code == 422


def test_trained_drivers_move_intended_outcomes(tmp_path, monkeypatch):
    _train_isolated(tmp_path, monkeypatch, n=420, seed=5, rounds=35)
    pin = (5.696, 50.851)
    off = infer(Treatment(typeId="datacentre", center=pin, cooling=False, buffer=False))
    cool = infer(Treatment(typeId="datacentre", center=pin, cooling=True, buffer=False))
    buffered = infer(Treatment(typeId="datacentre", center=pin, cooling=False, buffer=True))
    assert cool.outcomes.riverTempC.p50 <= off.outcomes.riverTempC.p50
    assert buffered.outcomes.habitatHa.p50 <= off.outcomes.habitatHa.p50

    quiet = infer(Treatment(typeId="wind", center=(5.85, 52.15)))
    busy = infer(
        Treatment(
            typeId="wind",
            center=(5.85, 52.15),
            nearbyTreatments=[
                NearbyTreatment(typeId="highway", center=(5.852, 52.151)),
                NearbyTreatment(typeId="industrial", center=(5.849, 52.149)),
            ],
        )
    )
    assert busy.outcomes.habitatHa.p50 >= quiet.outcomes.habitatHa.p50
