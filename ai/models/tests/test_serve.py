from __future__ import annotations

from fastapi.testclient import TestClient

from impact_models import paths
from impact_models.infer import load_boosters, load_cart_text
from impact_models.serve import app
from impact_models.train import train
from impact_models.warehouse import clear_warehouse_cache


def test_train_infer_http(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr(paths, "BOOSTERS_DIR", tmp_path / "boosters")
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", tmp_path / "empty-raw")
    clear_warehouse_cache()
    load_boosters.cache_clear()
    load_cart_text.cache_clear()
    metrics = train(n=360, seed=3, rounds=25)
    assert "habitatHa" in metrics["heads"]
    load_boosters.cache_clear()
    load_cart_text.cache_clear()

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    wind = client.post(
        "/infer",
        json={"typeId": "wind", "center": [5.6874, 50.8218], "horizonYear": 2030},
    )
    assert wind.status_code == 200
    body = wind.json()
    assert body["country"] in {"NL", "BE", "LU"}
    assert body["outcomes"]["habitatHa"]["p10"] <= body["outcomes"]["habitatHa"]["p90"]
    field = client.post(
        "/infer",
        json={"typeId": "wind", "center": [5.29, 52.13], "horizonYear": 2030},
    )
    assert field.status_code == 200
