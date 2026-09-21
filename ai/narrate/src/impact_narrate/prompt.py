from __future__ import annotations

from impact_narrate.schema import ImpactReport

SYSTEM = """You brief a Benelux planner on a modelled infrastructure treatment.
Use only quantities present in the JSON. Do not invent species, distances, hectares, temperatures, jobs, or tonnes.
Name only sites listed in the JSON. Mention the country field if present. Mention the p10-p90 range when an outcome includes those fields.
shapTop values are habitat prediction drivers from the habitatHa p50 model, not general impact drivers. Say "habitat prediction drivers" if you mention them.
net is the equal mean of the eight sector scores. Say that if you mention net.
scenarioEstimate is a synthetic recipe check, not a measured field outcome. Say so if you mention it.
Do not claim that cooling or a buffer reduced a number unless the JSON contains two complete outcome sets to compare.
If newsHeadlines is a non-empty list, you may cite those titles as context; do not invent other incidents.
Write plain English. No markdown headings. No bullet lists unless a sentence needs a short clause.
"""


def user_prompt(report: ImpactReport) -> str:
    return (
        "Turn this locked impact JSON into three fields:\n"
        "1) briefing: 4-6 sentences. State the supplied outcomes and whether cooling and the riparian buffer are on or off.\n"
        "2) sectorNotes: short sentences keyed by wildlife, landPollution, waterPollution, energy, jobs, carbon.\n"
        "3) recommendation: 1-2 sentences. Do not invent a mitigation improvement. Tell the reader to compare two model runs at this pin for a numerical benefit.\n"
        "Return JSON with keys briefing, sectorNotes, recommendation.\n\n"
        f"{report.model_dump_json()}"
    )
