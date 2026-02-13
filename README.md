# SweetWatch

Open source CGM monitoring with AI agent and Garmin integration.

## Features

- **LibreLinkUp Integration** - bezposrednie polaczenie z LibreLinkUp API
- **Web Dashboard** - podglad glukozy w przegladarce z wykresem 24h
- **REST API** - endpointy do integracji z innymi systemami
- **AI Agent** (Claude API) - analiza trendow i predykcje (opcjonalne)
- **Garmin Widget** - wyswietlanie glukozy na zegarku Fenix 6 Pro
- **Self-hosted** - Docker Compose, pelna kontrola nad danymi

## Quick Start

### 1. Konfiguracja

```bash
cp .env.example .env
```

Edytuj `.env`:

```env
# LibreLinkUp - WYMAGANE
LIBRE_USERNAME=twoj@email.com
LIBRE_PASSWORD=twoje_haslo
LIBRE_REGION=EU

# Opcjonalne
ANTHROPIC_API_KEY=sk-...  # dla analizy AI
APP_PORT=8000
```

### 2. Uruchomienie

```bash
docker compose up -d
```

### 3. Dostep

- **Dashboard:** http://localhost:8000
- **API docs:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

## API Endpoints

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/` | GET | Dashboard HTML |
| `/health` | GET | Status API |
| `/api/glucose/current` | GET | Aktualny odczyt glukozy |
| `/api/glucose/history` | GET | Historia (domyslnie 24h) |
| `/api/glucose/sync` | POST | Reczna synchronizacja z LibreLinkUp |

### Przyklady

```bash
# Aktualny odczyt
curl http://localhost:8000/api/glucose/current

# Historia ostatnich 12h
curl "http://localhost:8000/api/glucose/history?hours=12"

# Wymus synchronizacje
curl -X POST http://localhost:8000/api/glucose/sync
```

### Format odpowiedzi

```json
{
  "id": 123,
  "value": 120.0,
  "trend": 3,
  "trend_arrow": "→",
  "timestamp": "2026-02-13T12:00:00"
}
```

Trend values:
- `1` (↓↓) - szybki spadek
- `2` (↓) - spadek
- `3` (→) - stabilny
- `4` (↑) - wzrost
- `5` (↑↑) - szybki wzrost

## Konfiguracja Garmin

### Wymagania

- Garmin Connect IQ SDK
- Zegarek: Fenix 6 Pro (lub kompatybilny)

### Konfiguracja URL

Edytuj `garmin/sweetwatch-widget/source/SweetWatchView.mc`:

```monkey-c
// Zmien YOUR_SERVER na adres serwera
"http://YOUR_SERVER:8000/api/glucose/current"
```

### Kompilacja

```bash
cd garmin/sweetwatch-widget
# Uzyj Connect IQ SDK do kompilacji
monkeyc -d fenix6pro -o sweetwatch.prg -m manifest.xml source/*.mc
```

### Instalacja na zegarku

1. Skopiuj `sweetwatch.prg` do `GARMIN/Apps/` na zegarku
2. Lub uzyj Garmin Express / Connect IQ Store

## Deploy na serwerze

### Opcja 1: Docker na VPS

```bash
# Na serwerze
git clone <repo>
cd sweetwatch
cp .env.example .env
nano .env  # uzupelnij dane

docker compose up -d
```

### Opcja 2: Z usluga systemd

```bash
# /etc/systemd/system/sweetwatch.service
[Unit]
Description=SweetWatch CGM
After=docker.service

[Service]
WorkingDirectory=/opt/sweetwatch
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

### Opcja 3: Za reverse proxy (nginx)

```nginx
server {
    listen 443 ssl;
    server_name cgm.twojadomena.pl;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Architektura

```
src/sweetwatch/
├── api/           # FastAPI endpoints + schematy
│   ├── main.py    # Glowna aplikacja
│   ├── schemas.py # Pydantic modele
│   └── routers/   # Endpointy API
├── sources/       # Zrodla danych CGM
│   ├── base.py    # Abstrakcyjna klasa
│   └── librelinkup.py  # Klient LibreLinkUp
├── services/      # Logika biznesowa
│   └── glucose.py # Serwis glukozy
├── tasks/         # Background tasks
│   └── sync.py    # Synchronizacja co 5 min
├── agent/         # Claude AI analyzer
├── db/            # SQLAlchemy engine
├── models/        # Modele ORM
└── templates/     # Dashboard HTML

garmin/sweetwatch-widget/  # Monkey C widget
```

## Synchronizacja danych

- **Automatyczna:** co 5 minut (background task)
- **Reczna:** POST `/api/glucose/sync`
- **Dashboard:** przycisk "Synchronizuj"

Dane sa zapisywane w SQLite (`data/sweetwatch.db`).

## Development

```bash
# Lokalne srodowisko
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Testy
pytest -v

# Lub w Docker
docker compose run --rm sweetwatch sh -c "pip install pytest pytest-asyncio && pytest -v"
```

## Troubleshooting

### LibreLinkUp 403/400

- Sprawdz czy dane logowania sa poprawne
- Upewnij sie ze region jest prawidlowy (EU, US, etc.)
- Zaakceptuj regulamin w aplikacji LibreLinkUp

### Brak danych

```bash
# Sprawdz logi
docker compose logs -f sweetwatch

# Wymus sync
curl -X POST http://localhost:8000/api/glucose/sync
```

### Dashboard nie laduje

```bash
# Sprawdz czy kontener dziala
docker compose ps

# Restart
docker compose restart
```

## Stack

- Python 3.11+ / FastAPI / Uvicorn
- SQLite (default) / PostgreSQL (optional)
- Jinja2 + Chart.js (dashboard)
- Docker + Docker Compose
- Monkey C (Garmin widget)

## License

MIT
