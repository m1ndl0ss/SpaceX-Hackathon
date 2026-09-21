from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import httpx

from impact_narrate.fallback import template_briefing
from impact_narrate.prompt import SYSTEM, user_prompt
from impact_narrate.schema import Briefing, ImpactReport

_CACHE: dict[str, Briefing] = {}


def report_hash(report: ImpactReport) -> str:
    payload = report.model_dump(mode="json")
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _parse_llm_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    if "briefing" not in data or "recommendation" not in data:
        return None
    notes = data.get("sectorNotes") or {}
    if not isinstance(notes, dict):
        notes = {}
    data["sectorNotes"] = {str(k): str(v) for k, v in notes.items()}
    return data


def llm_briefing(report: ImpactReport) -> Briefing | None:
    api_key = os.environ.get("NARRATE_API_KEY", "").strip()
    if not api_key:
        return None
    base = os.environ.get("NARRATE_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("NARRATE_MODEL", "gpt-4o-mini")
    try:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": user_prompt(report)},
                    ],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
    except Exception:
        return None
    parsed = _parse_llm_json(content)
    if not parsed:
        return None
    return Briefing(
        briefing=str(parsed["briefing"]),
        sectorNotes=parsed["sectorNotes"],
        recommendation=str(parsed["recommendation"]),
        source="llm",
    )


def narrate(report: ImpactReport) -> Briefing:
    key = report_hash(report)
    cached = _CACHE.get(key)
    if cached:
        return cached
    briefing = llm_briefing(report) or template_briefing(report)
    _CACHE[key] = briefing
    return briefing
