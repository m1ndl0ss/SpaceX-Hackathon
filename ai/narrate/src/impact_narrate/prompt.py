from __future__ import annotations

from impact_narrate.schema import ImpactReport

SYSTEM = """You brief a Benelux planner on a modelled infrastructure treatment.
Use only quantities present in the JSON. Do not invent species, distances, hectares, temperatures, jobs, or tonnes.
Name only sites listed in the JSON. Mention the country field if present. Mention the p10-p90 range when an outcome includes those fields.
If newsHeadlines is a non-empty list, you may cite those titles as context; do not invent other incidents.
Write plain English. No markdown headings. No bullet lists unless a sentence needs a short clause.
"""


def user_prompt(report: ImpactReport) -> str:
    return (
        "Turn this locked impact JSON into three fields:\n"
        "1) briefing: 4-6 sentences.\n"
        "2) sectorNotes: short sentences keyed by wildlife, landPollution, waterPollution, energy, jobs, carbon.\n"
        "3) recommendation: 1-2 sentences on cooling and/or a riparian buffer only if those flags exist.\n"
        "Return JSON with keys briefing, sectorNotes, recommendation.\n\n"
        f"{report.model_dump_json()}"
    )
