from __future__ import annotations

import numpy as np

HEADS = ("habitatHa", "riverTempC", "vegStress", "energyIdx", "jobsFte", "tco2e")
NONNEGATIVE_HEADS = frozenset({"habitatHa", "riverTempC", "vegStress", "energyIdx", "jobsFte"})
QUANTILES = ("p10", "p50", "p90")
QUANTILE_ALPHAS = {"p10": 0.1, "p50": 0.5, "p90": 0.9}


def clamp_head_value(head: str, value: float) -> float:
    number = float(value)
    if head in NONNEGATIVE_HEADS:
        return max(0.0, number)
    return number


def order_quantiles(p10: float, p50: float, p90: float) -> tuple[float, float, float]:
    lo, mid, hi = sorted((float(p10), float(p50), float(p90)))
    return lo, mid, hi


def apply_api_quantiles(head: str, p10: float, p50: float, p90: float) -> tuple[float, float, float]:
    lo, mid, hi = order_quantiles(p10, p50, p90)
    return clamp_head_value(head, lo), clamp_head_value(head, mid), clamp_head_value(head, hi)


def apply_api_quantiles_arrays(
    head: str, p10: np.ndarray, p50: np.ndarray, p90: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    stacked = np.stack([np.asarray(p10, dtype=float), np.asarray(p50, dtype=float), np.asarray(p90, dtype=float)], axis=1)
    ordered = np.sort(stacked, axis=1)
    if head in NONNEGATIVE_HEADS:
        ordered = np.maximum(ordered, 0.0)
    return ordered[:, 0], ordered[:, 1], ordered[:, 2]


def pinball_loss(y: np.ndarray, q: np.ndarray, alpha: float) -> float:
    delta = np.asarray(y, dtype=float) - np.asarray(q, dtype=float)
    return float(np.mean(np.where(delta >= 0.0, alpha * delta, (alpha - 1.0) * delta)))


def median_abs_error(y: np.ndarray, pred: np.ndarray) -> float:
    return float(np.median(np.abs(np.asarray(y, dtype=float) - np.asarray(pred, dtype=float))))


def crossing_rate(p10: np.ndarray, p50: np.ndarray, p90: np.ndarray) -> float:
    p10 = np.asarray(p10, dtype=float)
    p50 = np.asarray(p50, dtype=float)
    p90 = np.asarray(p90, dtype=float)
    return float(np.mean((p10 > p50) | (p50 > p90) | (p10 > p90)))
