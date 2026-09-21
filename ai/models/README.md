# Benelux spatial impact models

Quantile LightGBM heads for infrastructure treatments in NL / BE / LU, plus a shallow CART explainer. A later HTTP client can `POST /infer` with a treatment and render the report.

Covariates are read from `data/raw/{name}_latest.json` when present (GBIF, roadkill, protected areas, water, OSM roads, Open-Meteo). Missing files become zeros plus `dataFlags`. Warehouse polygons replace the curated habitat/water list; if those files are empty, generate and infer still run on the small curated fallback. Labels stay a synthetic treatment recipe. Do not train on cell composite scores. News titles on the report are briefing metadata only.

## Install

```bash
cd ai/models
python -m pip install -e ".[dev]"
```

## Warehouse

Primary path: repo-root `data/raw/*_latest.json`. Live GBIF/roadkill fetch is fallback only:

```bash
impact-models-fetch
```

## Train

```bash
impact-models-train --n 6000 --rounds 120
```

Writes boosters to `artifacts/boosters/` and `artifacts/metrics.json`.

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
