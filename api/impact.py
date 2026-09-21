from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai" / "models" / "src"))


def _json(handler, code, payload):
    data = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _sectors_from_outcomes(treatment, outcomes):
    from impact_models.context import project_type
    from impact_models.features import lookup_sectors
    from impact_models.geo import clamp
    from impact_models.schema import Sectors

    lookup = lookup_sectors(treatment)
    habitat = outcomes.habitatHa.p50
    river = outcomes.riverTempC.p50
    stress = outcomes.vegStress.p50
    energy_idx = outcomes.energyIdx.p50
    jobs = outcomes.jobsFte.p50
    tco2e = outcomes.tco2e.p50
    energy_prior = float(project_type(treatment.typeId)["sectors"]["energy"])
    energy = clamp(-energy_idx / 1.35) if energy_prior < 0 else clamp((1.2 - energy_idx) / 0.15)
    return Sectors(
        wildlife=round(clamp(-habitat / 12.0), 2),
        landPollution=round(clamp(-stress / 4.0), 2),
        waterPollution=round(clamp(-river / 0.45), 2),
        energy=round(energy, 2),
        jobs=round(clamp(jobs / 10.0), 2),
        carbon=round(clamp(-tco2e / 120.0), 2),
        society=round(float(lookup["society"]), 2),
        noise=round(float(lookup["noise"]), 2),
    )


def _recipe_report(treatment_dict):
    from impact_models.features import country_code, data_flags, feature_row, hit_sites, nearby_headlines
    from impact_models.generate import recipe_labels
    from impact_models.outputs import HEADS, apply_api_quantiles
    from impact_models.schema import ImpactReport, Outcomes, Quantile, ScenarioEstimate, Treatment

    treatment = Treatment.model_validate(treatment_dict)
    row = feature_row(treatment, include_observations=True)
    estimate = recipe_labels(row)
    outcome_map = {}
    for head in HEADS:
        mid = float(estimate[head])
        span = max(0.08 * abs(mid) + 0.04, 0.02)
        lo, ordered, hi = apply_api_quantiles(head, mid - span, mid, mid + span)
        outcome_map[head] = Quantile(p10=lo, p50=ordered, p90=hi)
    outcomes = Outcomes(**outcome_map)
    sectors = _sectors_from_outcomes(treatment, outcomes)
    values = [
        sectors.wildlife, sectors.landPollution, sectors.waterPollution, sectors.energy,
        sectors.jobs, sectors.carbon, sectors.society, sectors.noise,
    ]
    drivers = sorted(
        ((name, float(row.get(name) or 0)) for name in ("habitat_proximity", "scale", "water_overlap", "gbif_suitability", "nearby_2km")),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    shap = [
        {"feature": name, "direction": "increase" if value >= 0 else "decrease", "value": round(value, 4)}
        for name, value in drivers[:3]
    ]
    return ImpactReport(
        typeId=treatment.typeId,
        center=treatment.center,
        horizonYear=treatment.horizonYear,
        country=country_code(treatment.center),
        mitigations={"cooling": treatment.cooling, "buffer": treatment.buffer},
        outcomes=outcomes,
        sectors=sectors,
        sites=hit_sites(treatment.center, treatment.typeId),
        shapTop=shap,
        explainer="Serverless recipe path used when LightGBM is unavailable.",
        net=round(sum(values) / len(values), 2),
        dataFlags=data_flags(),
        newsHeadlines=nearby_headlines(),
        scenarioEstimate=ScenarioEstimate(**{head: round(float(estimate[head]), 4) for head in HEADS}),
        labelKind="synthetic_scenario",
        shapTarget="habitatHa",
        netMethod="equal_mean_of_eight_sectors",
    ).model_dump()


def _infer(treatment_dict):
    try:
        from impact_models.infer import infer
        from impact_models.schema import Treatment
        return infer(Treatment.model_validate(treatment_dict)).model_dump()
    except Exception:
        return _recipe_report(treatment_dict)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        flags = {}
        try:
            from impact_models.warehouse import warehouse_flags
            flags = warehouse_flags()
        except Exception as exc:
            flags = {"error": str(exc)}
        _json(self, 200, {"ok": True, "warehouse": flags})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            _json(self, 400, {"detail": "Invalid JSON"})
            return
        try:
            _json(self, 200, _infer(body))
        except ValueError as exc:
            _json(self, 422, {"detail": str(exc)})
        except Exception as exc:
            _json(self, 500, {"detail": str(exc)})

    def log_message(self, format, *args):
        return
