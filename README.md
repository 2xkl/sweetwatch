# SweetWatch

Open source CGM monitoring with AI agent and Garmin integration.

## Features

- **LibreLinkUp API** integration - fetch real-time CGM data
- **AI Agent** (Claude API) - trend analysis and glucose predictions
- **Garmin Connect IQ Widget** (Monkey C) - display glucose on Fenix 6 Pro
- **Self-hosted** - Docker Compose, easy env var config

## Quick Start

```bash
cp .env.example .env
# Edit .env with your credentials
docker compose up -d
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Architecture

```
src/sweetwatch/
  api/        # FastAPI endpoints
  libre/      # LibreLinkUp API client
  agent/      # Claude AI trend analyzer
  db/         # Database engine & sessions
  models/     # SQLAlchemy models
garmin/       # Connect IQ widget (Monkey C)
infra/        # Terraform (optional cloud deploy)
```

## Stack

- Python 3.11+ / FastAPI
- SQLite (default) / PostgreSQL (optional)
- Docker + Docker Compose
- Monkey C (Garmin widget)
- Terraform (optional)

## License

MIT
