from __future__ import annotations

from fastapi.testclient import TestClient

from impact_narrate.client import _CACHE
from impact_narrate.fallback import template_briefing
from impact_narrate.schema import ImpactReport
from impact_narrate.serve import app

SAMPLE = {
    "typeId": "datacentre",
    "center": [5.696, 50.851],
    "horizonYear": 2030,
    "country": "NL",
    "mitigations": {"cooling": False, "buffer": False},
    "outcomes": {
        "habitatHa": {"p10": 8.0, "p50": 12.0, "p90": 18.0},
        "riverTempC": {"p10": 0.6, "p50": 1.1, "p90": 1.8},
        "vegStress": {"p10": 4.0, "p50": 6.0, "p90": 9.0},
        "energyIdx": {"p10": 5.0, "p50": 6.5, "p90": 8.0},
        "jobsFte": {"p10": 18.0, "p50": 24.0, "p90": 30.0},
        "tco2e": {"p10": 400.0, "p50": 520.0, "p90": 700.0},
    },
    "sectors": {
        "wildlife": -1.0,
        "landPollution": -1.5,
        "waterPollution": -2.4,
        "energy": -5.0,
        "jobs": 2.4,
        "carbon": -4.0,
    },
    "sites": [{"id": "maas", "name": "River Maas", "kind": "water", "distanceM": 80, "species": []}],
    "shapTop": [{"feature": "min_water_m", "direction": "increase", "value": 2.1}],
    "explainer": "min_water_m <= 400",
    "net": -1.2,
    "dataFlags": {"gbif": False, "roadkill": False},
    "newsHeadlines": [],
}


def test_template_contains_locked_numbers():
    report = ImpactReport.model_validate(SAMPLE)
    briefing = template_briefing(report)
    assert "12.0" in briefing.briefing
    assert "River Maas" in briefing.briefing
    assert "NL" in briefing.briefing
    assert "benelux" in briefing.briefing.lower() or "NL" in briefing.briefing
    assert "Habitat prediction drivers" in briefing.briefing
    assert "equal mean of the eight sector scores" in briefing.briefing
    assert "reduced" not in briefing.briefing.lower()
    assert "compare two model runs" in briefing.recommendation
    assert briefing.source == "template"
    assert "limburg" not in briefing.briefing.lower()

    with_news = ImpactReport.model_validate({**SAMPLE, "newsHeadlines": ["Otter crossing closed on N2"]})
    news_brief = template_briefing(with_news)
    assert "Otter crossing closed on N2" in news_brief.briefing


def test_narrate_http_fallback(monkeypatch):
    monkeypatch.delenv("NARRATE_API_KEY", raising=False)
    _CACHE.clear()
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    response = client.post("/narrate", json=SAMPLE)
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "template"
    assert "12.0" in body["briefing"]
    again = client.post("/narrate", json=SAMPLE)
    assert again.json() == body
