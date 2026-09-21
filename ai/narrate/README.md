# Impact narrate

Turns a locked `ImpactReport` JSON into planner copy for a Benelux briefing. It does not compute numbers.

## Install

```bash
cd ai/narrate
python -m pip install -e ".[dev]"
```

## Serve

```bash
impact-narrate-serve --port 8766
```

Optional LLM (OpenAI-compatible):

```bash
set NARRATE_API_KEY=...
set NARRATE_BASE_URL=https://api.openai.com/v1
set NARRATE_MODEL=gpt-4o-mini
```

Without a key, a template fills the same JSON shape.

## Call

```bash
curl -s http://127.0.0.1:8766/narrate \
  -H "Content-Type: application/json" \
  -d @report.json
```

`report.json` is the body returned by `POST /infer` on the models service.

Response:

```json
{
  "briefing": "...",
  "sectorNotes": {"wildlife": "...", "jobs": "..."},
  "recommendation": "...",
  "source": "template"
}
```

`source` is `"llm"` or `"template"`. Responses are cached by report hash. Use only sites, country, and quantities in the report; `newsHeadlines` may be cited if present.
