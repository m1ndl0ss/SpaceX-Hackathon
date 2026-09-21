# Review of the supplied impact models

Reviewed 21 September 2026. This review covers the checked-in `ai/models` artifacts, feature extraction, synthetic label recipe, stored evaluation results, and their integration into the app. No team model or training artifact was changed or retrained.

**Verdict: suitable for an explicitly labeled exploratory demo; not validated for forecasting the ecological impact of real projects or approving development.** The regressors learn a hand-written synthetic recipe with added noise. Their held-out scores measure how well they reproduce that recipe, not real-world impact accuracy.

## What is now connected

The app calls the team's existing `POST /infer` service. Its eight supported types are wind, solar, industrial plant, highway, housing, dam/hydropower, power line, and data centre. Inputs are a point location, relative scale (0.4–2.0), assessment year (2026–2040), cooling/buffer flags, and up to three nearby projects. The UI limits cooling to the two project types where closed-loop process cooling is meaningful.

The UI shows all six returned outcomes and their p10/p50/p90 predictions: habitat loss, river warming, vegetation stress, energy pressure, employment, and carbon. Mitigation comparisons make two actual model calls at the same location, scale, year, and neighborhood. The app also displays nearby features, habitat prediction contributions, per-type synthetic validation statistics, missing-source warnings, and saved input/output snapshots.

The original direct MW, water-withdrawal, and hectare formulas were removed because none is a model feature. The app now collects these and other type-specific quantities through a separately labeled, uncalibrated demo conversion into `scale`. It averages ratios to illustrative reference values, with visible clipping to 0.4–2.0. This does not give the stored models independent physical inputs or establish their validity. Exact assumptions and examples are documented in [PHYSICAL_INPUTS.md](PHYSICAL_INPUTS.md). The former no-project baseline and fabricated time trajectory were removed. The map's radius comes from the type catalog and is labeled a screening area, not a damage plume.

## Material findings

### 1. No empirical outcome validation — high priority

`generate.py:recipe_labels` derives targets from manually assigned project-type scores and multipliers. `physical_labels` adds Gaussian noise of `0.08 * abs(value) + 0.04`. The ecological and socioeconomic coefficients have no calibration provenance in this package. GBIF, roadkill, protected-area, water, road, and weather data provide input features; they are not measured post-construction impact targets.

The 6,000 rows are split into 4,199 training, 901 validation, and 900 test examples, stratified by type. They are generated from the same recipe and shared spatial warehouse. This is a reasonable synthetic surrogate test but provides neither geographic holdout evidence nor an empirical assessment of causal project effects. Geographic and temporal independence require separate evaluation designs; ordinary random splits can give optimistic estimates for spatial prediction. See [scikit-learn's evaluation guidance](https://scikit-learn.org/stable/modules/cross_validation.html) and this [spatial cross-validation evaluation](https://arxiv.org/abs/2303.07334).

**Integration response:** visible synthetic-scenario labeling; no real-world safety claim or approval recommendation. Physical input conversions are explicitly identified as demo assumptions, with their arithmetic and reference values exposed. Stored validation metrics do not validate this new conversion.

### 2. Quantile ranges are only partially calibrated — high priority

Stored, postprocessed held-out metrics from `artifacts/metrics.json`:

| Output | p50 MAE | p10–p90 coverage (80% target) | Quantile crossings before sorting |
|---|---:|---:|---:|
| Habitat loss | 3.94 ha | 80.3% | 6.6% |
| River warming | 0.064 °C | 74.4% | 2.3% |
| Vegetation stress | 0.363 points | 77.0% | 3.7% |
| Energy index | 0.150 | 78.1% | 1.4% |
| Employment | 0.940 FTE | 79.3% | 3.7% |
| Carbon | 36.72 tCO₂e | 81.0% | 4.7% |

Per-type coverage is worse in places: data-centre energy 65.1% (109 test cases), dam river temperature 66.7% (117), and industrial vegetation stress 67.0% (115). Sorting the three quantile estimates and clipping nonnegative outputs enforces range ordering, but does not establish calibration or physical validity. Even correct synthetic coverage would not establish real-world coverage.

**Integration response:** display the returned ranges directly, show actual per-type coverage, and flag outcomes below 70% coverage. Do not call these guaranteed 80% confidence intervals or infer a mitigation-effect confidence interval by subtracting marginal quantiles.

### 3. Units and physical interpretation are incomplete — high priority

- `energyIdx` is a synthetic, unitless index. It is not €/MWh or a megawatt estimate.
- `tco2e` is generated from type scores, scale, and year factors; its accounting period and system boundary are unspecified. It cannot be labeled annual emissions or lifecycle emissions.
- Habitat, river, and vegetation labels have no horizon-year dependence. The year changes synthetic jobs and carbon assumptions; it does not produce an ecological or climate trajectory.
- A point and fixed catalog radius represent highways, power lines, and dams. Route geometry, catchment flow, discharge transport, operational intensity, species population responses, and project-specific footprint are not modeled.
- The `net` score equally averages eight arbitrary normalized sectors; some values saturate at the clamp limits. It is not a validated policy utility or ecological safety score.

**Integration response:** correct units, no manufactured timeline or changing damage radius, and no overall go/no-go score.

### 4. Spatial screening has confirmed defects — high priority for real use

`geo.py:point_in_polygon` checks the exterior ring only. An audit point inside a polygon hole is incorrectly assigned distance zero. MultiPolygon centroid selection uses the first polygon, and warehouse clipping uses that representative point; this can omit or misclassify multipart features. Country assignment uses overlapping bounding boxes, not borders, and defaults to the nearest box outside them. The API accepts `(0, 0)` and assigns it to Belgium.

**Integration response:** the app validates finite coordinates against the model's approximate training boxes, labels screening as approximate, and states that no returned nearby features does not imply ecological clearance. Accurate boundaries and geometry fixes require changes and re-evaluation in the team's model pipeline.

### 5. Behavioral probes passed most checks, but mitigation is not guaranteed

A reproducible audit ran **290 predictions** using the stored artifacts across eight types and five locations (Dordrecht, Limburg, Namur, Luxembourg, Ardennes), including scale extremes, selected years, buffers, cooling for industrial/data-centre projects, and a nearby highway.

- All 18 boosters' feature-name order matched the inference feature list.
- No invalid or reversed output ranges appeared after API postprocessing.
- No tested scale, cooling, or nearby-project habitat reversals appeared.
- Three buffer cases increased river-temperature p50: wind and solar at Luxembourg by about 0.021 °C, and power line at Luxembourg by about 0.010 °C. These are small but contradict the intended buffer direction.
- Seventeen of 40 type/location pairs varied habitat p50 by more than 0.1 ha across 2026/2035/2040, despite the recipe's year independence. The maximum drift was 0.285 ha. Treat this as surrogate variation, not ecological trend evidence.

These finite probes do not prove global monotonicity. The UI reports comparison results as returned rather than forcing a positive mitigation narrative.

Full cases and values: [model-audit.json](model-audit.json). The team's feature, generation, and warehouse tests also passed: **19 tests**. These tests confirm software behavior, not ecological validity.

### 6. Source coverage and runtime reproducibility need care

The training summary lists 907 kept species records, 212 roadkill records, 400 protected-area records, 34 water features, 50 roads, and 5 weather sites. Seven species-specific features are constant. Source-availability flags are global, not assurance that a particular site has adequate observations. Current nearest-site precipitation/snow is used without a future weather scenario. There are no news records; news is metadata, not model evidence.

The stored CART surrogate has 10.94 ha MAE versus the habitat booster and R² 0.695. It should not replace the main prediction or be treated as an exact explanation. The app shows the booster's prediction contributions instead. These are model explanations, not causal attributions; LightGBM documents `predict_contrib` in its [parameter reference](https://lightgbm.readthedocs.io/en/latest/Parameters.html#predict_contrib).

The CART pickle was written with scikit-learn 1.8.0. The initial dependency install selected 1.9.1 and emitted an incompatibility warning. The app setup now constrains scikit-learn to **1.8.0**; loading an estimator across versions is unsupported according to [scikit-learn's persistence guidance](https://scikit-learn.org/stable/model_persistence.html#security-maintainability-limitations).

## Recommended work before real decision use

1. Define each output's physical meaning, timescale, spatial support, and accounting boundary; replace arbitrary labels with observed or independently validated process-model outcomes.
2. Add explicit project capacity, footprint, water/heat discharge, route/catchment geometry, and operational profiles where appropriate. Calibrate rather than guessing conversions to `scale`.
3. Fix polygon holes, multipart handling, border assignment, input-domain validation, and local source-coverage diagnostics.
4. Validate on independent real projects, with geographic and temporal holdouts; calibrate intervals per project type and document out-of-distribution behavior.
5. Test physical invariants and mitigation effects over a broader domain. Pin package versions and record artifact/data fingerprints.

## Reproduce

From `app/`:

```bash
npm run models:setup                 # Python 3.11+; dependencies live only in app/.model-venv
npm run models:sync                  # refresh selectors and stored validation metadata
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .model-venv/bin/python -B scripts/audit_models.py
PYTHONPATH=../ai/models/src OMP_NUM_THREADS=1 .model-venv/bin/python -B -m pytest ../ai/models/tests/test_features.py ../ai/models/tests/test_generate.py ../ai/models/tests/test_warehouse.py -p no:cacheprovider -q
npm test
npm run build
```
