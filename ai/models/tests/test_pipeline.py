from __future__ import annotations

from fastapi.testclient import TestClient

from impact_models import paths
from impact_models.infer import load_boosters, load_cart, load_cart_text
from impact_models.serve import app as models_app
from impact_models.train import train
from impact_models.warehouse import clear_warehouse_cache
from impact_narrate.client import _CACHE
from impact_narrate.serve import app as narrate_app


def test_infer_then_narrate(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr(paths, "BOOSTERS_DIR", tmp_path / "boosters")
    monkeypatch.setattr(paths, "WAREHOUSE_DIR", tmp_path / "empty-raw")
    monkeypatch.delenv("NARRATE_API_KEY", raising=False)
    clear_warehouse_cache()
    load_boosters.cache_clear()
    load_cart.cache_clear()
    load_cart_text.cache_clear()
    train(n=280, seed=11, rounds=20)
    load_boosters.cache_clear()
    load_cart.cache_clear()
    load_cart_text.cache_clear()
    _CACHE.clear()

    models = TestClient(models_app)
    maas = models.post(
        "/infer",
        json={
            "typeId": "datacentre",
            "center": [5.696, 50.851],
            "horizonYear": 2030,
            "cooling": False,
            "buffer": False,
        },
    )
    assert maas.status_code == 200
    payload = maas.json()
    assert any(site["kind"] == "water" for site in payload["sites"]) or payload["outcomes"]["riverTempC"]["p50"] >= 0
    assert any(site["id"] == "maas" for site in payload["sites"])
    assert payload.get("labelKind") == "synthetic_scenario"
    assert "habitatHa" in (payload.get("scenarioEstimate") or {})
    narrate = TestClient(narrate_app)
    briefing = narrate.post("/narrate", json=payload)
    assert briefing.status_code == 200
    text = briefing.json()["briefing"].lower()
    assert "benelux" in text or payload["country"].lower() in text
    if not any(site["id"] == "sint-pietersberg" for site in payload["sites"]):
        assert "limburg" not in text

    ardennes = models.post(
        "/infer",
        json={"typeId": "wind", "center": [6.13, 50.52], "horizonYear": 2030},
    )
    assert ardennes.status_code == 200
    ardennes_body = ardennes.json()
    assert any(site["id"] == "hautes-fagnes" for site in ardennes_body["sites"])
    ardennes_brief = narrate.post("/narrate", json=ardennes_body)
    assert ardennes_brief.status_code == 200
    ardennes_text = ardennes_brief.json()["briefing"].lower()
    if not any(site["id"] == "sint-pietersberg" for site in ardennes_body["sites"]):
        assert "limburg" not in ardennes_text
    assert {site["id"] for site in payload["sites"]} != {site["id"] for site in ardennes_body["sites"]}
