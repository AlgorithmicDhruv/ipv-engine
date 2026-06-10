# IPV Engine — Independent Price Verification System

A backend system for verifying financial instrument valuations against independent market price sources. Built to support Global Markets risk control workflows where trader-submitted prices must be reconciled against third-party market data before positions are marked to market.

## What It Does

Traders submit end-of-day valuations for financial instruments (equities, FX forwards, interest rate swaps). This system ingests those submissions, pulls independent market prices from a separate source, computes the variance, and flags any breach exceeding a configurable threshold. Results are stored in a relational database and exposed via REST API for downstream consumption by risk dashboards or reporting tools.

## Architecture

```
Market Price Feed (Redis)
        |
        v
  Sync Service (Python)
        |
        v
PostgreSQL (Oracle-compatible schema)
        |
        v
  Flask REST API
        |
        v
  Angular 17 Dashboard
```

- **Sync Service**: pulls raw price records from Redis (simulating a NoSQL market data feed) and writes normalized records into PostgreSQL
- **Flask API**: exposes endpoints for submitting trader valuations, retrieving IPV results, and querying breach reports
- **PostgreSQL schema**: designed to be compatible with Oracle SQL conventions (no SERIAL, uses SEQUENCE; explicit schema namespacing)
- **Angular dashboard**: consumes the REST API and renders a data-grid showing instrument-level price variances and breach flags

## Tech Stack

- Python 3.11, Flask, SQLAlchemy (OOP model layer)
- PostgreSQL 15 (Oracle-compatible schema conventions)
- Redis 7 (NoSQL price feed simulation)
- Angular 17
- Docker, Docker Compose
- pytest for unit and integration tests

## Project Structure

```
ipv-engine/
├── backend/
│   ├── app/
│   │   ├── models/         # OOP SQLAlchemy models
│   │   ├── routes/         # Flask REST endpoints
│   │   ├── services/       # Business logic (pricing, reconciliation)
│   │   └── utils/          # DB session, config, logging
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Angular 17 app
├── infra/
│   └── docker-compose.yml
└── docs/
    └── api.md
```

## Running Locally

```bash
# Start all services
docker compose -f infra/docker-compose.yml up --build

# API runs on http://localhost:5000
# Angular dev server on http://localhost:4200
# PostgreSQL on localhost:5432
# Redis on localhost:6379
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/valuations | Submit trader valuation |
| GET | /api/v1/valuations/{instrument_id} | Get valuation history |
| GET | /api/v1/ipv/results | Get reconciliation results |
| GET | /api/v1/ipv/breaches | Get breach report |
| POST | /api/v1/prices/sync | Trigger price sync from Redis feed |
| GET | /api/v1/instruments | List all instruments |

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Configuration

Environment variables (set in `.env` or Docker Compose):

```
DATABASE_URL=postgresql://ipv_user:password@localhost:5432/ipv_db
REDIS_URL=redis://localhost:6379/0
BREACH_THRESHOLD_PCT=0.5
LOG_LEVEL=INFO
```
