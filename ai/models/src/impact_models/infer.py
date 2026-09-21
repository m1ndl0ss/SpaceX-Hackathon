from __future__ import annotations

from functools import lru_cache

import lightgbm as lgb
import numpy as np

from impact_models.context import project_type
from impact_models.features import FEATURE_COLUMNS, data_flags, feature_row, hit_sites, lookup_sectors, vectorize
from impact_models.generate import HEADS
from impact_models.geo import clamp
from impact_models import paths
from impact_models.schema import ImpactReport, Outcomes, Quantile, Sectors, ShapItem, Treatment

QUANTILES = ("p10", "p50", "p90")


class ArtifactError(FileNotFoundError):
    pass


@lru_cache(maxsize=1)
def load_boosters() -> dict[str, lgb.Booster]:
    boosters: dict[str, lgb.Booster] = {}
    for head in HEADS:
        for label in QUANTILES:
            path = paths.BOOSTERS_DIR / f"{head}_{label}.txt"
            if not path.exists():
                raise ArtifactError(f"Missing booster {path.name}. Train first.")
            boosters[f"{head}_{label}"] = lgb.Booster(model_file=str(path))
    return boosters


@lru_cache(maxsize=1)
def load_cart_text() -> str:
    path = paths.ARTIFACTS_DIR / "habitat_cart.txt"
    if not path.exists():
        return ""
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return "\n".join(lines[:12])


def _ordered(p10: float, p50: float, p90: float) -> Quantile:
    lo, mid, hi = sorted((p10, p50, p90))
    return Quantile(p10=float(lo), p50=float(mid), p90=float(hi))


def _predict_head(boosters: dict[str, lgb.Booster], head: str, x: np.ndarray) -> Quantile:
    values = [float(boosters[f"{head}_{label}"].predict(x)[0]) for label in QUANTILES]
    return _ordered(*values)


def _shap_top(boosters: dict[str, lgb.Booster], x: np.ndarray, k: int = 3) -> list[ShapItem]:
    contrib = boosters["habitatHa_p50"].predict(x, pred_contrib=True)[0]
    pairs = list(zip(FEATURE_COLUMNS, contrib[:-1]))
    pairs.sort(key=lambda item: abs(item[1]), reverse=True)
    items: list[ShapItem] = []
    for name, value in pairs[:k]:
        items.append(
            ShapItem(
                feature=name,
                direction="increase" if value >= 0 else "decrease",
                value=round(float(value), 4),
            )
        )
    return items


def sectors_from_outcomes(treatment: Treatment, outcomes: Outcomes) -> Sectors:
    lookup = lookup_sectors(treatment)
    habitat = outcomes.habitatHa.p50
    river = outcomes.riverTempC.p50
    stress = outcomes.vegStress.p50
    energy_idx = outcomes.energyIdx.p50
    jobs = outcomes.jobsFte.p50
    tco2e = outcomes.tco2e.p50
    energy_prior = float(project_type(treatment.typeId)["sectors"]["energy"])
    if energy_prior < 0:
        energy = clamp(-energy_idx / 1.35)
    else:
        energy = clamp((1.2 - energy_idx) / 0.15)
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


def infer(treatment: Treatment) -> ImpactReport:
    boosters = load_boosters()
    row = feature_row(treatment, include_observations=True)
    x = np.array([vectorize(row)], dtype=float)
    outcome_map = {head: _predict_head(boosters, head, x) for head in HEADS}
    outcomes = Outcomes(**outcome_map)
    sectors = sectors_from_outcomes(treatment, outcomes)
    sector_values = [
        sectors.wildlife,
        sectors.landPollution,
        sectors.waterPollution,
        sectors.energy,
        sectors.jobs,
        sectors.carbon,
        sectors.society,
        sectors.noise,
    ]
    return ImpactReport(
        typeId=treatment.typeId,
        center=treatment.center,
        horizonYear=treatment.horizonYear,
        mitigations={"cooling": treatment.cooling, "buffer": treatment.buffer},
        outcomes=outcomes,
        sectors=sectors,
        sites=hit_sites(treatment.center, treatment.typeId),
        shapTop=_shap_top(boosters, x),
        explainer=load_cart_text(),
        net=round(sum(sector_values) / len(sector_values), 2),
        dataFlags=data_flags(),
    )
