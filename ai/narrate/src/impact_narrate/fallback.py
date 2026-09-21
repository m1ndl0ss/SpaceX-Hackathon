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
    briefing = (
        f"A {label} at {report.center[1]:.4f} N, {report.center[0]:.4f} E is modelled to {report.horizonYear}. "
        f"Suitable habitat change is {_fmt(hab.p50)} ha (p10 {_fmt(hab.p10)}, p90 {_fmt(hab.p90)}). "
        f"River temperature pressure is {_fmt(river.p50)} C (p10 {_fmt(river.p10)}, p90 {_fmt(river.p90)}). "
        f"Employment is {_fmt(jobs.p50)} FTE and net tCO2e/year is {_fmt(carbon.p50, 0)}. "
        f"Sites in range: {sites}. Closed-loop cooling is {cooling}; riparian buffer is {buffer}. "
        f"Leading drivers: {shap}."
    )
    notes = {
        "wildlife": f"Wildlife sector {report.sectors.wildlife:+.1f}; habitat { _fmt(hab.p50)} ha.",
        "landPollution": f"Land sector {report.sectors.landPollution:+.1f}; vegetation stress { _fmt(report.outcomes.vegStress.p50)}.",
        "waterPollution": f"Water sector {report.sectors.waterPollution:+.1f}; river temperature { _fmt(river.p50)} C.",
        "energy": f"Energy sector {report.sectors.energy:+.1f}; pressure index { _fmt(report.outcomes.energyIdx.p50)}.",
        "jobs": f"Jobs sector {report.sectors.jobs:+.1f}; {_fmt(jobs.p50)} FTE at this horizon.",
        "carbon": f"Carbon sector {report.sectors.carbon:+.1f}; {_fmt(carbon.p50, 0)} tCO2e/year.",
    }
    if report.mitigations.get("cooling") and report.mitigations.get("buffer"):
        rec = "Cooling and a riparian buffer are both on in this run; compare against an unmitigated treatment at the same pin."
    elif report.sectors.waterPollution < 0 or report.sectors.wildlife < 0:
        rec = "A riparian buffer and, where water is hit, closed-loop cooling are the first mitigations to compare."
    else:
        rec = "This placement is mixed to net-positive on the modelled sectors; keep the p10-p90 habitat band in the file."
    return Briefing(briefing=briefing, sectorNotes=notes, recommendation=rec, source="template")
