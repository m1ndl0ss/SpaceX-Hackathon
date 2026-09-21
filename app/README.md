# Yosemite — conservation coordination

A persistent browser demo connecting activists with a government dashboard. All application code, sample records, and tests live in `app`.

## Run

```bash
npm install
npm run models:setup # one-time Python 3.11+ environment for simulation
npm run dev
```

Open the URL printed by Vite. Use **Switch workspace** to move between roles. Use the same origin (hostname and port) in each tab to share records.

- **Activist:** enter a name and profile, submit a violation with location, observation time, urgency, details, and an optional evidence link. Follow its response history. Browse calls for help, join a crew, read government updates, or withdraw a signup.
- **Government:** review and filter the violation inbox, post a response and status, request volunteers for a specific violation, or publish an independent call for help. See each roster, post updates, close signups, and complete or cancel an action.
- The overview derives its counts, priorities, and activity from the same records. Resolving a violation is separate from completing a volunteer action. Closed violations can be reopened with an explanation.

## Persistence and demo scope

Reports, calls, profiles, signups, and response history are stored in `localStorage` under `yosemite.workspace.v1`. Refreshing preserves records; tabs on the same origin receive updates. Each tab remembers its active role/profile using `sessionStorage`. Returning with the same profile name restores that activist's identity and records. Profiles are demo identities, not authenticated accounts.

Sample records are created on first use, with upcoming action dates relative to that first visit. A full, closed, cancelled, completed, or past action cannot accept new signups. Withdrawing frees capacity. Errors from full or unavailable browser storage are shown without discarding the form.

This demo does not share data across browsers/devices or send email, alerts, invitations, or external submissions. Evidence is a link; files are not uploaded. Clearing this site's browser data removes its saved workspace.

## Government project simulation

Open **Simulation** in the Government workspace. Select one of the eight types from the team's model catalog, enter its physical quantities, locate the project using a preset, coordinates, or the map, and set the assessment year. Inputs adapt to the type: water withdrawal, electricity demand, generation capacity, land area, route length, home count, or dam flow. Unit selectors preserve the quantity when switching between units. Example presets fill illustrative values and remain editable. Add up to three nearby projects and optionally compare habitat buffers or closed-loop cooling (industrial plants and data centres). **Run assessment** calls the existing stored LightGBM models in `../ai/models`; it does not train new models.

The physical inputs use an explicitly labeled **demo approximation**: divide each value by its illustrative reference and average those ratios into the existing model's scale parameter, limited to 0.4–2.0. The form discloses the references, method, and any range clipping. Water, land, and capacity effects are not independently modeled. **How inputs affect the estimate** also offers a manual-factor mode for legacy assessments; measurements in that mode are recorded only. See [physical input assumptions](docs/PHYSICAL_INPUTS.md).

The results show the assessed physical inputs, six outcomes with p10/p50/p90 estimates, an actual with/without mitigation comparison, nearby model features, prediction contributions, and stored validation statistics. **Save assessment** keeps the exact inputs, conversion assumptions, results, and comparison view in this browser under `yosemite.impact-assessments.v1`. Changing inputs marks old results as stale until a new run succeeds. Previously saved assessments retain their original manual factor; no physical quantities are invented for them.

Vite automatically starts the team's Python service on `127.0.0.1:8765` and proxies `/api/impact` in both dev and preview. Dependencies live in `app/.model-venv`; setup leaves the team sources and artifacts unchanged. If Python is not on PATH, use `npm run models:setup -- /path/to/python3.12`. Set `MODEL_PYTHON` to use a different existing runtime, or launch Vite with `IMPACT_MODEL_URL=http://host:port` to use an existing compatible service instead. These are server environment variables, not `VITE_` browser variables.

On Windows, setup also detects `python` and the `py -3` launcher, and uses `.model-venv/Scripts/python.exe`. If using the repository's existing Python environment, run `npm run models:setup -- ..\.venv\Scripts\python.exe` from `app`. Restart Vite after setup. To check the service, open `http://127.0.0.1:8765/health`; a connection failure means the runtime has not started.

`npm run models:sync` refreshes selectors, artifact fingerprints, and evaluation metadata from the supplied model files; it also runs before dev and build. An external service must use the matching model artifacts. For a static production deployment, run the model service separately and route `/api/impact/*` to it with the prefix removed; the static bundle cannot launch Python.

**Validity:** these are models of synthetic scenario labels, not validated real-world ecological forecasts. Scale has no calibrated conversion to MW, footprint, or water demand. Carbon has no defined accounting period. Spatial screening and some uncertainty ranges have known weaknesses. See the [model review](docs/MODEL_REVIEW.md) and [290-case stored-model audit](docs/model-audit.json).

## Maps

Maps use Mapbox. Copy `.env.example` to `.env`, add a public `VITE_MAPBOX_TOKEN`, and restart Vite. Reports, calls, and dashboard controls work without a map token. Conservation layers and the sample map incident are illustrative; free-text report locations are not geocoded.

## Validation

```bash
npm test       # coordination workflows, model contracts, comparisons, persistence, errors
npm run build # production bundle in dist/
npm run preview
```

To repeat the stored-model audit without retraining:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .model-venv/bin/python -B scripts/audit_models.py
```
