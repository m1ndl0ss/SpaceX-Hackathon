# SpaceX Hackathon

Three top-level folders:

- `app/` — frontend
- `data/` — cached JSON, seed catalog, GIS caches (`data/app.db` is gitignored)
- `ai/` — Python: collectors, scoring, API, models, narrate

`ai/` is the Python root (`from collectors...`, `from api...`). Paths resolve data as `repo_root/data` via `Path(__file__).resolve().parents`.

## API

```bash
cd ai
pip install -r requirements.txt
uvicorn api.main:app --port 8000 --reload
```

Persistence smoke test: `python api/test_persist.py`

## Collect

```bash
cd ai
python run.py
```
