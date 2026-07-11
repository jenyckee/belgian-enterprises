# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Local FastAPI service over the Belgian KBO (Crossroads Bank for Enterprises) open-data
CSV snapshot, stored in PostgreSQL. Some endpoints also proxy the NBB CBSO API to fetch
annual-account (accounting) data by enterprise number.

## Commands

```bash
# Start local PostgreSQL (exposed on host port 5434 to avoid conflicts)
docker compose up -d

# Install deps
python -m pip install -r requirements.txt

# Ingest the KBO CSV snapshot into PostgreSQL (DROPS and recreates all tables)
python db/ingest.py

# Run the API (http://127.0.0.1:8000, docs at /docs)
uvicorn api.main:app --reload

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "message"

# Ad-hoc integration checks against the live NBB API (not pytest; run directly)
python test_accounting_data.py   # prints pass/fail for NBB references + accountingdata
python debug_nbb_api.py
```

There is no lint/test toolchain configured. `test_accounting_data.py` uses FastAPI's
`TestClient` but is a script with `print`-based assertions, not a pytest suite — run it
with `python`, not `pytest`.

## Environment

Config is loaded via `db/database.py` in this order: `.env.local` (override=True) then
`.env` (override=False). **Use `.env.local` for local development** — the repo also
contains a remote `.env` that must not be overwritten. `.env` and `.env.local` are
gitignored.

- `DATABASE_URL` (or `POSTGRES_*` parts) — defaults to `postgresql+psycopg://kbo:kbo@localhost:5434/kbo`
- `AUTHENTIC_DATA_PRIMARY_KEY` / `AUTHENTIC_DATA_SECONDARY_KEY` — NBB CBSO API subscription key, required for `/references` and `/accountingdata` endpoints (sent as `NBB-CBSO-Subscription-Key` header)

Note: `alembic.ini` hardcodes `sqlalchemy.url` to the same local DSN; it does not read
env vars, so update it if the DB location changes.

## Architecture

Three layers, all importing through the project root on `sys.path`:

- **`db/`** — data layer. `database.py` builds the engine/session and the shared
  `Base`. `models.py` defines the SQLAlchemy ORM tables. `ingest.py` bulk-loads the CSVs.
- **`api/`** — web layer. `main.py` builds the FastAPI app (permissive CORS, `/` health
  check) and mounts `routes.py`. `schemas.py` holds the Pydantic response models.

### Data model and the entity_number join key

The KBO data has two kinds of numbered entities: **enterprises** (`enterprise_number`)
and **establishments** (`establishment_number`). Satellite tables — `addresses`,
`contacts`, `denominations`, `activities` — do **not** distinguish the two: they key off a
generic `entity_number` that may be *either* an enterprise or an establishment number.
This is why `GET /enterprises?nace=...` (in `routes.py`) uses raw SQL that joins
`activities.entity_number` against both `enterprises` and (via `establishments`)
back to the owning enterprise. Keep this dual-key behavior in mind when adding queries.

### Ingestion (`db/ingest.py`)

- `main()` **drops and recreates all tables** on every run, then loads each CSV in
  `CSV_MAP` order. It is a full reload, not incremental.
- CSV headers are PascalCase (`EnterpriseNumber`); `KEY_MAPPING` + `normalize_record`
  translate them to the snake_case ORM column names and coerce empty strings to `NULL`.
- Rows are inserted in batches of `BATCH_SIZE` (5000) using PostgreSQL
  `INSERT ... ON CONFLICT DO NOTHING` on the primary key.
- Autoincrement `id` PKs are dropped from the row dict so the DB assigns them.
- Schema is defined by the ORM (`Base.metadata.create_all`), **not** by Alembic — so a
  fresh ingest already has the current indexes. Alembic migrations exist mainly to add
  indexes to an already-populated DB without a full re-ingest.

### Indexes and NACE search

`activities` carries a covering btree index with `varchar_pattern_ops` on `nace_code`
so the `nace_code LIKE 'XX%'` prefix search in `/enterprises` stays fast. When changing
that query's filter columns, keep the covering index (`ix_activities_nace_code_classification`)
in sync.

### NBB CBSO proxy endpoints (`routes.py`)

`/enterprise/{n}/references` and `/enterprise/{n}/accountingdata/{year}` call the live
NBB API with `urllib` (no client library), then hand-map the PascalCase JSON response
into the Pydantic models in `schemas.py`. The accountingdata flow first fetches
`/references`, finds the deposit whose `ExerciseDates.startDate` year matches, then
fetches `/deposit/{ReferenceNumber}/accountingData` with `Accept: application/x.jsonxbrl`.
Enterprise numbers are passed without dots.

These curl requests are known to be correct

```
curl -v -X GET "https://ws.cbso.nbb.be/authentic/deposit/0689.587.747/accountingData" \
  -H "Accept: application/pdf" \
  -H "X-Request-Id: b76b0f37-bdaf-4f22-aee3-aabc391427b6" \
  -H "Cache-Control: no-cache" \
  -H "NBB-CBSO-Subscription-Key: $AUTHENTIC_DATA_PRIMARY_API_KEY" \
  -o accounting_data.pdf
```
```
curl -v -X GET "https://ws.cbso.nbb.be/authentic/deposit/2025-00570954/accountingData" \
  -H "Accept: application/x.jsonxbrl" \
  -H "X-Request-Id: b76b0f37-bdaf-4f22-aee3-aabc391427b6" \
  -H "Cache-Control: no-cache" \
  -H "NBB-CBSO-Subscription-Key: $AUTHENTIC_DATA_PRIMARY_API_KEY" \
```

## Data

Download the KBO CSV snapshot from
https://kbopub.economie.fgov.be/kbo-open-data/affiliation/xml/?files and unzip into
`data/`. Expected files: `enterprise.csv`, `establishment.csv`, `address.csv`,
`contact.csv`, `denomination.csv`, `activity.csv`, `branch.csv`, `code.csv`, `meta.csv`.
CSVs are gitignored.
