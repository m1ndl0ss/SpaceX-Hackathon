from __future__ import annotations

import time
from typing import Any

import httpx

from impact_models.context import bbox, load_context
from impact_models.observations import ROADKILL_POINTS, save_points

GBIF_SEARCH = "https://api.gbif.org/v1/occurrence/search"
DATASET_KEYS = [
    "65908f95-5ab6-48d9-bf6d-6da274ed730e",
    "90d9e8a0-0c54-4175-9c9c-7d139eb0c0e5",
]
PAGE = 300
COUNTRIES = ("NL", "BE", "LU")


def _names() -> list[str]:
    return [item["scientificName"] for item in load_context()["roadkillGroups"]]


def fetch_roadkill() -> tuple[int, str | None]:
    west, south, east, north = bbox()
    rows: list[dict[str, Any]] = []
    names = {name.lower() for name in _names()}
    try:
        with httpx.Client(headers={"User-Agent": "impact-models/0.1"}) as client:
            for dataset in DATASET_KEYS:
                for country in COUNTRIES:
                    offset = 0
                    while offset < 4000:
                        params = {
                            "datasetKey": dataset,
                            "country": country,
                            "hasCoordinate": "true",
                            "limit": PAGE,
                            "offset": offset,
                            "decimalLongitude": f"{west},{east}",
                            "decimalLatitude": f"{south},{north}",
                        }
                        response = client.get(GBIF_SEARCH, params=params, timeout=30.0)
                        if response.status_code == 404:
                            break
                        response.raise_for_status()
                        results = (response.json().get("results") or [])
                        if not results:
                            break
                        for record in results:
                            scientific = str(record.get("species") or record.get("scientificName") or "")
                            stem = scientific.lower()
                            if not any(name in stem for name in names):
                                continue
                            lng = record.get("decimalLongitude")
                            lat = record.get("decimalLatitude")
                            if lng is None or lat is None:
                                continue
                            taxon_id = stem.split(" ")[0] + "_" + (stem.split(" ")[1] if " " in stem else "sp")
                            rows.append(
                                {
                                    "lng": float(lng),
                                    "lat": float(lat),
                                    "taxon_id": taxon_id,
                                    "scientificName": scientific,
                                }
                            )
                        if len(results) < PAGE:
                            break
                        offset += PAGE
                        time.sleep(0.15)
        save_points(ROADKILL_POINTS, rows)
        return len(rows), None
    except Exception as exc:
        save_points(ROADKILL_POINTS, [])
        return 0, str(exc)
