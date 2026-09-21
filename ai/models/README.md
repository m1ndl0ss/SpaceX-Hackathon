# Benelux spatial impact models

Quantile LightGBM heads for infrastructure treatments in NL / BE / LU, plus a shallow CART explainer. A later HTTP client can `POST /infer` with a treatment and render the report.

Covariates are read from repo-root `data/*_latest.json` (the same files the app serves). GBIF occurrences come from `habitats_latest.json` (with `gbif_latest.json` as a fallback). `data/raw/` is used only if the collector folder is the default warehouse and a source is missing there. Missing files become zeros plus `has_*` availability features and `dataFlags`. Warehouse polygons replace the curated habitat/water list; if those files are empty, generate and infer still run on the small curated fallback.

Labels stay a **synthetic treatment recipe**. `scenarioEstimate` on the report is that noise-free recipe at the same pin — not a field measurement. Do not train on cell composite scores. News titles on the report are briefing metadata only.

Assumptions in the recipe:

- Nearby projects (about half of training rows) add habitat, river, and energy pressure from `nearby_500m` / `nearby_2km` / `nearby_highway_2km`. Neighbor mitigations are ignored.
- Weather (precip/snow) lowers `vegStress` and slightly lowers `riverTempC` only when `has_open_meteo` is 1. Habitat, jobs, energy, and carbon stay independent of weather.
- Cooling lowers river temperature pressure; a riparian buffer lowers habitat / vegetation / river pressure. Numerical mitigation claims need two model runs at the same pin.

## Install

```bash
cd ai/models
python -m pip install -e ".[dev]"
```

## Warehouse

Primary path: repo-root `data/habitats_latest.json`, `data/roadkill_latest.json`, `data/protected_areas_latest.json`, `data/water_latest.json`, `data/osm_roads_latest.json`, `data/open_meteo_latest.json`. Live GBIF/roadkill fetch is fallback only:

```bash
impact-models-fetch
```

## Train

```bash
impact-models-train --n 6000 --rounds 120
```

Writes boosters to `artifacts/boosters/`, `artifacts/metrics.json` (held-out test scores after the same quantile sort and nonnegative clamps as the API), and `artifacts/training_summary.json` (record counts, missing sources, constant features).

Training samples `horizonYear` 2026–2040 and `scale` 0.4–2.0, matching the API. `type_idx` and `country_idx` are categorical. CART is fit to the habitat p50 booster and the report `explainer` is that sample's decision path.

## Serve

```bash
impact-models-serve --port 8765
```

Health: `GET http://127.0.0.1:8765/health`

### Infer

Limburg pin:

```bash
curl -s http://127.0.0.1:8765/infer \
  -H "Content-Type: application/json" \
  -d '{"typeId":"wind","center":[5.6874,50.8218],"horizonYear":2030,"cooling":false,"buffer":false}'
```

Namur:

```bash
curl -s http://127.0.0.1:8765/infer \
  -H "Content-Type: application/json" \
  -d '{"typeId":"highway","center":[4.87,50.47],"horizonYear":2030}'
```

Luxembourg City:

```bash
curl -s http://127.0.0.1:8765/infer \
  -H "Content-Type: application/json" \
  -d '{"typeId":"datacentre","center":[6.13,49.61],"horizonYear":2035,"cooling":true}'
```

Pipe the JSON to `POST http://127.0.0.1:8766/narrate`.
