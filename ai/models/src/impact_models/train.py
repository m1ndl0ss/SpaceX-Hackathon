from __future__ import annotations

import argparse
import json

import joblib
import lightgbm as lgb
import numpy as np
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor, export_text

from impact_models.features import FEATURE_COLUMNS
from impact_models.generate import HEADS, generate_frame
from impact_models.observations import load_fetch_status
from impact_models import paths
from impact_models.paths import ensure_data_dirs

QUANTILES = (("p10", 0.1), ("p50", 0.5), ("p90", 0.9))


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
    train_set = lgb.Dataset(x_train, label=y_train, feature_name=list(FEATURE_COLUMNS), free_raw_data=False)
    val_set = lgb.Dataset(x_val, label=y_val, reference=train_set, feature_name=list(FEATURE_COLUMNS), free_raw_data=False)
    return lgb.train(
        params,
        train_set,
        num_boost_round=rounds,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(20, verbose=False)],
    )


def train(n: int = 6000, seed: int = 7, rounds: int = 120) -> dict:
    ensure_data_dirs()
    frame = generate_frame(n=n, seed=seed, include_observations=True)
    x = frame[list(FEATURE_COLUMNS)].to_numpy(dtype=float)
    metrics: dict = {"n": int(len(frame)), "heads": {}, "fetch": load_fetch_status()}
    x_train, x_val, idx_train, idx_val = train_test_split(x, np.arange(len(frame)), test_size=0.2, random_state=seed)

    for head in HEADS:
        y = frame[head].to_numpy(dtype=float)
        y_train, y_val = y[idx_train], y[idx_val]
        head_metrics = {}
        for label, alpha in QUANTILES:
            booster = _train_quantile(x_train, y_train, x_val, y_val, alpha, rounds)
            path = paths.BOOSTERS_DIR / f"{head}_{label}.txt"
            booster.save_model(str(path))
            pred = booster.predict(x_val)
            head_metrics[label] = {"mae": float(mean_absolute_error(y_val, pred))}
        metrics["heads"][head] = head_metrics

    y_hab = frame["habitatHa"].to_numpy(dtype=float)
    cart = DecisionTreeRegressor(max_depth=4, random_state=seed, min_samples_leaf=30)
    cart.fit(x_train, y_hab[idx_train])
    joblib.dump(cart, paths.ARTIFACTS_DIR / "habitat_cart.joblib")
    tree_text = export_text(cart, feature_names=list(FEATURE_COLUMNS), max_depth=4)
    (paths.ARTIFACTS_DIR / "habitat_cart.txt").write_text(tree_text, encoding="utf-8")
    metrics["cartMae"] = float(mean_absolute_error(y_hab[idx_val], cart.predict(x_val)))

    (paths.ARTIFACTS_DIR / "feature_list.json").write_text(json.dumps(list(FEATURE_COLUMNS), indent=2), encoding="utf-8")
    (paths.ARTIFACTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
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
