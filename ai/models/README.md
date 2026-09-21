# Limburg spatial impact models

Quantile LightGBM heads for infrastructure treatments in southern Limburg, plus a shallow CART explainer. A later HTTP client can `POST /infer` with a treatment and render the report.

## Install

```bash
cd ai/models
python -m pip install -e ".[dev]"
```

## Data (optional)

```bash
impact-models-fetch
```

Pulls GBIF occurrences for local taxa (CC0 / CC BY only) and roadkill records for NL/BE. Writes `data/processed/`. If the network fails, training still runs with zeroed observation columns; `artifacts/metrics.json` records the flag.

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

```bash
curl -s http://127.0.0.1:8765/infer ^
  -H "Content-Type: application/json" ^
  -d "{\"typeId\":\"wind\",\"center\":[5.6874,50.8218],\"horizonYear\":2030,\"cooling\":false,\"buffer\":false}"
```

Unix:

```bash
curl -s http://127.0.0.1:8765/infer \
  -H "Content-Type: application/json" \
  -d '{"typeId":"wind","center":[5.6874,50.8218],"horizonYear":2030,"cooling":false,"buffer":false}'
```

Body fields: `typeId`, `center` `[lng,lat]`, `horizonYear`, `cooling`, `buffer`, optional `scale`, optional `nearbyTreatments`.

Response is an `ImpactReport`: quantile outcomes (`habitatHa`, `riverTempC`, `vegStress`, `energyIdx`, `jobsFte`, `tco2e`), sector scores, sites in range, top drivers, CART snippet.

Pipe that JSON to the narrate service (`POST http://127.0.0.1:8766/narrate`) for briefing copy.
