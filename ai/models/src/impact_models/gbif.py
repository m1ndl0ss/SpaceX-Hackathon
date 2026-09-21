from __future__ import annotations

import time
from typing import Any

import httpx

from impact_models.context import bbox, taxa
from impact_models.observations import ALLOWED_LICENSES, GBIF_POINTS, license_ok, save_points

GBIF_SEARCH = "https://api.gbif.org/v1/occurrence/search"
PAGE = 300


def _bbox_params() -> dict[str, Any]:
    west, south, east, north = bbox()
    return {
        "decimalLongitude": f"{west},{east}",
        "decimalLatitude": f"{south},{north}",
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "limit": PAGE,
    }


def _license_ok_record(record: dict[str, Any]) -> bool:
    license_value = str(record.get("license") or record.get("licenseCode") or "")
    return license_ok(license_value) or any(tag in license_value.lower() for tag in ALLOWED_LICENSES)


def fetch_taxon(client: httpx.Client, taxon: dict[str, Any], max_records: int = 1500) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while offset < max_records:
        params = _bbox_params()
        params["taxonKey"] = taxon["taxonKey"]
        params["offset"] = offset
        response = client.get(GBIF_SEARCH, params=params, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        if not results:
            break
        for record in results:
            if not _license_ok_record(record):
                continue
            lng = record.get("decimalLongitude")
            lat = record.get("decimalLatitude")
            if lng is None or lat is None:
                continue
            rows.append(
                {
                    "lng": float(lng),
                    "lat": float(lat),
                    "taxon_id": taxon["id"],
                    "scientificName": taxon["scientificName"],
                }
            )
        if len(results) < PAGE:
            break
        offset += PAGE
        time.sleep(0.15)
    return rows


def fetch_gbif() -> tuple[int, str | None]:
    rows: list[dict[str, Any]] = []
    try:
        with httpx.Client(headers={"User-Agent": "impact-models/0.1"}) as client:
            for taxon in taxa():
                rows.extend(fetch_taxon(client, taxon))
        save_points(GBIF_POINTS, rows)
        return len(rows), None
    except Exception as exc:  # network or parse failure: keep going on zeros
        save_points(GBIF_POINTS, [])
        return 0, str(exc)
