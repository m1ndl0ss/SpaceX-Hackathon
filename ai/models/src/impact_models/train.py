from __future__ import annotations

import argparse
import json
from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor, export_text

from impact_models.features import CATEGORICAL_FEATURES, FEATURE_COLUMNS, TYPE_INDEX
from impact_models.generate import generate_frame
from impact_models.observations import load_fetch_status
from impact_models.outputs import (
    HEADS,
    QUANTILE_ALPHAS,
    QUANTILES,
    apply_api_quantiles_arrays,
    crossing_rate,
    median_abs_error,
    pinball_loss,
)
from impact_models import paths
from impact_models.paths import ensure_data_dirs
from impact_models.warehouse import warehouse_flags, warehouse_intake_report

COUNTRY_NAMES = {0: "NL", 1: "BE", 2: "LU"}
TYPE_NAMES = {index: name for name, index in TYPE_INDEX.items()}
SOURCE_FEATURE_GROUPS = {
    "gbif": ("gbif_suitability", "gbif_count_2km"),
    "roadkill": ("roadkill_intensity_2km", "roadkill_count_2km"),
    "osm_roads": ("min_road_km",),
    "open_meteo": ("precip_mm", "snow_mm"),
}


def split_indices(frame: pd.DataFrame, seed: int = 7) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    idx = np.arange(len(frame))
    stratify = frame["type_idx"].to_numpy(dtype=int) if "type_idx" in frame.columns else None
    try:
        trainval, test = train_test_split(idx, test_size=0.15, random_state=seed, stratify=stratify)
        strat_trainval = stratify[trainval] if stratify is not None else None
        train, val = train_test_split(trainval, test_size=0.15 / 0.85, random_state=seed, stratify=strat_trainval)
    except ValueError:
        trainval, test = train_test_split(idx, test_size=0.15, random_state=seed)
        train, val = train_test_split(trainval, test_size=0.15 / 0.85, random_state=seed)
    return np.asarray(train), np.asarray(val), np.asarray(test)


def _train_quantile(x_train, y_train, x_val, y_val, alpha: float, rounds: int) -> lgb.Booster:
    params = {
        "objective": "quantile",
        "alpha": alpha,
        "learning_rate": 0.05,
        "num_leaves": 24,
        "min_data_in_leaf": 20,
        "feature_fraction": 0.9,
        "verbosity": -1,
        "seed": 7,
    }
    train_set = lgb.Dataset(
        x_train,
        label=y_train,
        feature_name=list(FEATURE_COLUMNS),
        categorical_feature=list(CATEGORICAL_FEATURES),
        free_raw_data=False,
    )
    val_set = lgb.Dataset(
        x_val,
        label=y_val,
        reference=train_set,
        feature_name=list(FEATURE_COLUMNS),
        categorical_feature=list(CATEGORICAL_FEATURES),
        free_raw_data=False,
    )
    return lgb.train(
        params,
        train_set,
        num_boost_round=rounds,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(20, verbose=False)],
    )


def _counts(series: pd.Series, names: dict[int, str] | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value, n in series.value_counts().sort_index().items():
        key = names.get(int(value), str(int(value))) if names is not None else str(value)
        counts[str(key)] = int(n)
    return counts


def build_training_summary(frame: pd.DataFrame, idx_train, idx_val, idx_test) -> dict[str, Any]:
    flags = warehouse_flags()
    constant = [name for name in FEATURE_COLUMNS if int(frame[name].nunique(dropna=False)) <= 1]
    nunique = {name: int(frame[name].nunique(dropna=False)) for name in FEATURE_COLUMNS}
    missing = [name for name, present in flags.items() if not present]
    warnings: list[str] = []
    for source, columns in SOURCE_FEATURE_GROUPS.items():
        if not flags.get(source):
            warnings.append(f"{source} missing")
            continue
        if all(int(frame[col].nunique(dropna=False)) <= 1 for col in columns if col in frame.columns):
            warnings.append(f"{source} present but constant in the training frame")
    summary = {
        "n": int(len(frame)),
        "split": {"train": int(len(idx_train)), "val": int(len(idx_val)), "test": int(len(idx_test))},
        "sources": warehouse_intake_report(),
        "missingSources": missing,
        "constantFeatures": constant,
        "featureNunique": nunique,
        "typeCounts": _counts(frame["type_idx"], TYPE_NAMES),
        "countryCounts": _counts(frame["country_idx"], COUNTRY_NAMES),
        "horizonCounts": _counts(frame["horizon_year"].astype(int)),
        "sourceWarnings": warnings,
        "fetch": load_fetch_status(),
    }
    if warnings:
        print("training source warnings:", "; ".join(warnings))
    return summary


def evaluate_head(head: str, y: np.ndarray, raw: dict[str, np.ndarray], types: np.ndarray) -> dict[str, Any]:
    crossing = crossing_rate(raw["p10"], raw["p50"], raw["p90"])
    p10, p50, p90 = apply_api_quantiles_arrays(head, raw["p10"], raw["p50"], raw["p90"])
    inside = (y >= p10) & (y <= p90)
    by_type: dict[str, Any] = {}
    for type_idx in sorted(set(types.tolist())):
        mask = types == type_idx
        if not np.any(mask):
            continue
        name = TYPE_NAMES.get(int(type_idx), str(int(type_idx)))
        coverage = float(inside[mask].mean())
        mae = float(mean_absolute_error(y[mask], p50[mask]))
        by_type[name] = {
            "n": int(mask.sum()),
            "coverage80": coverage,
            "mae": mae,
            "meanWidth": float(np.mean(p90[mask] - p10[mask])),
            "flag": bool(abs(coverage - 0.80) > 0.15 or mae > 3.0 * float(mean_absolute_error(y, p50) + 1e-9)),
        }
    return {
        "crossingBeforeSort": crossing,
        "coverage80": float(inside.mean()),
        "meanWidth": float(np.mean(p90 - p10)),
        "byType": by_type,
        "p10": {"mae": float(mean_absolute_error(y, p10)), "pinball": pinball_loss(y, p10, QUANTILE_ALPHAS["p10"])},
        "p50": {
            "mae": float(mean_absolute_error(y, p50)),
            "medianMae": median_abs_error(y, p50),
            "pinball": pinball_loss(y, p50, QUANTILE_ALPHAS["p50"]),
        },
        "p90": {"mae": float(mean_absolute_error(y, p90)), "pinball": pinball_loss(y, p90, QUANTILE_ALPHAS["p90"])},
    }


def train(n: int = 6000, seed: int = 7, rounds: int = 120) -> dict:
    ensure_data_dirs()
    frame = generate_frame(n=n, seed=seed, include_observations=True)
    x = frame[list(FEATURE_COLUMNS)].to_numpy(dtype=float)
    idx_train, idx_val, idx_test = split_indices(frame, seed=seed)
    x_train, x_val, x_test = x[idx_train], x[idx_val], x[idx_test]
    types_test = frame["type_idx"].to_numpy(dtype=int)[idx_test]
    summary = build_training_summary(frame, idx_train, idx_val, idx_test)
    metrics: dict = {"n": int(len(frame)), "heads": {}, "fetch": summary["fetch"], "split": summary["split"]}

    habitat_p50 = None
    for head in HEADS:
        y = frame[head].to_numpy(dtype=float)
        y_train, y_val, y_test = y[idx_train], y[idx_val], y[idx_test]
        raw: dict[str, np.ndarray] = {}
        for label in QUANTILES:
            booster = _train_quantile(x_train, y_train, x_val, y_val, QUANTILE_ALPHAS[label], rounds)
            path = paths.BOOSTERS_DIR / f"{head}_{label}.txt"
            booster.save_model(str(path))
            raw[label] = np.asarray(booster.predict(x_test), dtype=float)
            if head == "habitatHa" and label == "p50":
                habitat_p50 = booster
        metrics["heads"][head] = evaluate_head(head, y_test, raw, types_test)

    y_hab_train = frame["habitatHa"].to_numpy(dtype=float)[idx_train]
    cart = DecisionTreeRegressor(max_depth=4, random_state=seed, min_samples_leaf=30)
    if habitat_p50 is not None:
        cart_target = np.asarray(habitat_p50.predict(x_train), dtype=float)
        booster_test = np.asarray(habitat_p50.predict(x_test), dtype=float)
    else:
        cart_target = y_hab_train
        booster_test = frame["habitatHa"].to_numpy(dtype=float)[idx_test]
    cart.fit(x_train, cart_target)
    joblib.dump(cart, paths.ARTIFACTS_DIR / "habitat_cart.joblib")
    tree_text = export_text(cart, feature_names=list(FEATURE_COLUMNS), max_depth=4)
    (paths.ARTIFACTS_DIR / "habitat_cart.txt").write_text(tree_text, encoding="utf-8")
    cart_test = cart.predict(x_test)
    metrics["cartVsBoosterMae"] = float(mean_absolute_error(booster_test, cart_test))
    metrics["cartVsBoosterR2"] = float(r2_score(booster_test, cart_test))
    metrics["cartMae"] = float(mean_absolute_error(frame["habitatHa"].to_numpy(dtype=float)[idx_test], cart_test))

    (paths.ARTIFACTS_DIR / "feature_list.json").write_text(json.dumps(list(FEATURE_COLUMNS), indent=2), encoding="utf-8")
    (paths.ARTIFACTS_DIR / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (paths.ARTIFACTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({"n": summary["n"], "missingSources": summary["missingSources"], "sourceWarnings": summary["sourceWarnings"]}, indent=2))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train quantile LightGBM heads and a shallow CART explainer.")
    parser.add_argument("--n", type=int, default=6000)
    parser.add_argument("--rounds", type=int, default=120)
    args = parser.parse_args()
    metrics = train(n=args.n, rounds=args.rounds)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
