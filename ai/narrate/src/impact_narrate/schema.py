from __future__ import annotations

from pydantic import BaseModel, Field


class Quantile(BaseModel):
    p10: float
    p50: float
    p90: float


class Outcomes(BaseModel):
    habitatHa: Quantile
    riverTempC: Quantile
    vegStress: Quantile
    energyIdx: Quantile
    jobsFte: Quantile
    tco2e: Quantile


class ScenarioEstimate(BaseModel):
    habitatHa: float = 0.0
    riverTempC: float = 0.0
    vegStress: float = 0.0
    energyIdx: float = 0.0
    jobsFte: float = 0.0
    tco2e: float = 0.0


class Sectors(BaseModel):
    wildlife: float
    landPollution: float
    waterPollution: float
    energy: float
    jobs: float
    carbon: float
    society: float | None = None
    noise: float | None = None


class Site(BaseModel):
    id: str
    name: str
    kind: str
    distanceM: int | None = None
    species: list[str] = Field(default_factory=list)


class ShapItem(BaseModel):
    feature: str
    direction: str
    value: float


class ImpactReport(BaseModel):
    typeId: str
    center: tuple[float, float]
    horizonYear: int
    country: str = ""
    mitigations: dict[str, bool] = Field(default_factory=dict)
    outcomes: Outcomes
    sectors: Sectors
    sites: list[Site] = Field(default_factory=list)
    shapTop: list[ShapItem] = Field(default_factory=list)
    explainer: str = ""
    net: float = 0.0
    dataFlags: dict[str, bool] = Field(default_factory=dict)
    newsHeadlines: list[str] = Field(default_factory=list)
    scenarioEstimate: ScenarioEstimate | None = None
    labelKind: str = "synthetic_scenario"
    shapTarget: str = "habitatHa"
    netMethod: str = "equal_mean_of_eight_sectors"


class Briefing(BaseModel):
    briefing: str
    sectorNotes: dict[str, str]
    recommendation: str
    source: str
