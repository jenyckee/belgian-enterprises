# KBO FastAPI Service

This repository provides a local PostgreSQL-backed FastAPI service for KBO open data.

## Setup

1. Start local PostgreSQL with Docker Compose:

```bash
docker compose up -d
```

1. Create a local environment file:

```bash
cp .env.example .env.local
```

1. The Docker Postgres service is exposed on host port `5434` to avoid conflicts with existing local services.
2. Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

1. Ingest the CSV snapshot into PostgreSQL:

```bash
python db/ingest.py
```

1. Start the FastAPI application:

```bash
uvicorn api.main:app --reload
```

## Default local endpoints

- `GET /` - health check
- `GET /enterprise/{enterprise_number}`
- `GET /enterprise/{enterprise_number}/establishments`
- `GET /enterprise/{enterprise_number}/contact`
- `GET /enterprise/{enterprise_number}/denominations`
- `GET /establishment/{establishment_number}`

## Notes

- Local development should use `.env.local` so the existing remote `.env` file does not take precedence.
- The data folder contains the KBO CSV snapshot used for ingestion.

## Data

The project assumes data under `/data`. Download the KBO CSV snapshot from https://kbopub.economie.fgov.be/kbo-open-data/affiliation/xml/?files
and unzip the contents into `/data`.

The folder should contain the following CSV files:
```
/data/
    activity.csv
    address.csv
    branch.csv
    code.csv
    contact.csv
    denomination.csv
    enterprise.csv
    establishment.csv
    meta.csv
```