from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

TypeId = Literal[
    "wind",
    "solar",
    "industrial",
    "highway",
    "housing",
    "dam",
    "powerline",
    "datacentre",
]


class NearbyTreatment(BaseModel):
    typeId: TypeId
    center: tuple[float, float]


class Treatment(BaseModel):
    typeId: TypeId
    center: tuple[float, float]
    horizonYear: int = 2030
    cooling: bool = False
    buffer: bool = False
    scale: float = 1.0
    nearbyTreatments: list[NearbyTreatment] = Field(default_factory=list)

    @field_validator("horizonYear")
    @classmethod
    def year_in_range(cls, value: int) -> int:
        if value < 2026 or value > 2040:
            raise ValueError("horizonYear must be between 2026 and 2040")
        return value

    @field_validator("scale")
    @classmethod
    def scale_in_range(cls, value: float) -> float:
        if value < 0.4 or value > 2.0:
            raise ValueError("scale must be between 0.4 and 2.0")
        return float(value)

    @field_validator("center")
    @classmethod
    def lng_lat(cls, value: tuple[float, float]) -> tuple[float, float]:
        lng, lat = value
        if not (-180 <= lng <= 180 and -90 <= lat <= 90):
            raise ValueError("center must be (lng, lat)")
        return (float(lng), float(lat))


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
    habitatHa: float
    riverTempC: float
    vegStress: float
    energyIdx: float
    jobsFte: float
    tco2e: float


class Sectors(BaseModel):
    wildlife: float
    landPollution: float
    waterPollution: float
    energy: float
    jobs: float
    carbon: float
    society: float
    noise: float


class Site(BaseModel):
    id: str
    name: str
    kind: Literal["habitat", "water"]
    distanceM: int | None = None
    species: list[str] = Field(default_factory=list)


class ShapItem(BaseModel):
    feature: str
    direction: Literal["increase", "decrease"]
    value: float


class ImpactReport(BaseModel):
    typeId: TypeId
    center: tuple[float, float]
    horizonYear: int
    country: str = "NL"
    mitigations: dict[str, bool]
    outcomes: Outcomes
    sectors: Sectors
    sites: list[Site]
    shapTop: list[ShapItem]
    explainer: str
    net: float
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
    source: Literal["llm", "template"]
