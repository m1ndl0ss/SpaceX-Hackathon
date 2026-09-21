from __future__ import annotations

from impact_narrate.schema import Briefing, ImpactReport

TYPE_LABELS = {
    "wind": "wind turbine",
    "solar": "solar farm",
    "industrial": "industrial plant",
    "highway": "highway",
    "housing": "housing",
    "dam": "dam",
    "powerline": "power line",
    "datacentre": "datacentre",
}


def _fmt(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def template_briefing(report: ImpactReport) -> Briefing:
    label = TYPE_LABELS.get(report.typeId, report.typeId)
    hab = report.outcomes.habitatHa
    river = report.outcomes.riverTempC
    jobs = report.outcomes.jobsFte
    carbon = report.outcomes.tco2e
    site_names = [site.name for site in report.sites] or ["no named habitat or water body in range"]
    sites = ", ".join(site_names[:4])
    cooling = "on" if report.mitigations.get("cooling") else "off"
    buffer = "on" if report.mitigations.get("buffer") else "off"
    shap = ", ".join(f"{item.feature} ({item.direction})" for item in report.shapTop[:3]) or "type and distance"
    country = report.country or "Benelux"
    news = "; ".join(report.newsHeadlines[:2])
    briefing = (
        f"A {label} in {country} at {report.center[1]:.4f} N, {report.center[0]:.4f} E is modelled to {report.horizonYear}. "
        f"Suitable habitat change is {_fmt(hab.p50)} ha (p10 {_fmt(hab.p10)}, p90 {_fmt(hab.p90)}). "
        f"River temperature pressure is {_fmt(river.p50)} C (p10 {_fmt(river.p10)}, p90 {_fmt(river.p90)}). "
        f"Employment is {_fmt(jobs.p50)} FTE and net tCO2e/year is {_fmt(carbon.p50, 0)}. "
        f"Sites in range: {sites}. Closed-loop cooling is {cooling}; riparian buffer is {buffer}. "
        f"Habitat prediction drivers: {shap}. "
        f"Net {report.net:+.2f} is the equal mean of the eight sector scores."
    )
    estimate = report.scenarioEstimate
    if estimate is not None:
        briefing += (
            f" A synthetic scenario recipe (not a field measurement) estimates "
            f"habitat {_fmt(estimate.habitatHa)} ha and river {_fmt(estimate.riverTempC)} C at this pin."
        )
    if news:
        briefing += f" Related headlines on file: {news}."
    notes = {
        "wildlife": f"Wildlife sector {report.sectors.wildlife:+.1f}; habitat { _fmt(hab.p50)} ha.",
        "landPollution": f"Land sector {report.sectors.landPollution:+.1f}; vegetation stress { _fmt(report.outcomes.vegStress.p50)}.",
        "waterPollution": f"Water sector {report.sectors.waterPollution:+.1f}; river temperature { _fmt(river.p50)} C.",
        "energy": f"Energy sector {report.sectors.energy:+.1f}; pressure index { _fmt(report.outcomes.energyIdx.p50)}.",
        "jobs": f"Jobs sector {report.sectors.jobs:+.1f}; {_fmt(jobs.p50)} FTE at this horizon.",
        "carbon": f"Carbon sector {report.sectors.carbon:+.1f}; {_fmt(carbon.p50, 0)} tCO2e/year.",
    }
    rec = (
        "These figures are from this single model run. "
        "For a numerical mitigation benefit, compare two model runs at this pin with cooling or a riparian buffer on vs off."
    )
    return Briefing(briefing=briefing, sectorNotes=notes, recommendation=rec, source="template")
