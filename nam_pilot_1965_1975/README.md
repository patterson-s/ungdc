# NAM Discourse Pilot — 1965-1975

Test-scale implementation of `../nam_discourse_plan.md`, scoped to 1965-1975 and built on a
flat-file JSON substrate (no Postgres) so it stays fully isolated from the live `ungdc_db`/web app.

## Status

- [x] NAM membership data built + spot-checked (`data/nam_membership.json`, `data/nam_membership_notes.md`)
- [x] Speech subset extracted with `nam_flag` joined in (`data/speeches_1965_1975.jsonl`, 1233 speeches, 138 countries, 45.7% NAM-flagged)
- [x] Country metadata built for matched-control sampling (`data/country_metadata.json`)
- [ ] Agent pipeline (`src/nam/`) — see build order below

**Before running the agent loop**, read `data/nam_membership_notes.md` — it lists open historical
judgment calls (Chile post-1973-coup, Argentina's 1973 accession, Yemen north/south coding) that
need a one-time human sign-off.

## Setup

```
pip install cohere
set COHERE_API_KEY=...        # PowerShell: $env:COHERE_API_KEY = "..."
```

## Rebuilding the data files

```
python src/build_speeches.py
python src/build_country_metadata.py
```

## Running the pilot

```
python -m src.nam.cli run-batch --year 1973     # smoke test first
python -m src.nam.cli questions list
python -m src.nam.cli grid show
```

See `../nam_discourse_plan.md` for the full architecture (agent roles, schema, non-goals) and
the saved plan at the top of this repo's planning history for the JSON-substrate adaptation,
model choices (Cohere Command A / Command A Reasoning), and the autonomy/escalation tiers.
