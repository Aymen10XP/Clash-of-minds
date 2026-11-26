# Clash of Minds - Installation and Execution Guide

This procedure is the reproducible third-party installation path required by the project brief. Commands target Windows PowerShell from the repository root.

## 1. Prerequisites

- Git
- Node.js 24 and npm 11, or compatible supported versions
- Python 3.12
- Docker Desktop with Linux containers
- Chrome and Firefox are supplied by the Cypress Docker image for automated compatibility checks

## 2. Install dependencies

```powershell
npm install
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r server\requirements-dev.txt
Copy-Item server\.env.example server\.env
```

The development requirements include runtime packages plus coverage, Bandit, and pip-audit.

## 3. Initialize the database and demo accounts

Start Docker Desktop, then run:

```powershell
npm run seed:demo
```

The command starts PostgreSQL, applies Django migrations, loads six topics and thirty quiz questions, and creates three local-only permission profiles:

| Profile | Username | Default local password | Access |
| --- | --- | --- | --- |
| Player | `demo_player` | `PlayerDemo!2026` | Player routes and owned gameplay data |
| Staff operator | `demo_admin` | `AdminDemo!2026` | Custom staff console, dashboard, question creation, user deactivation |
| Superuser | `demo_superuser` | `SuperDemo!2026` | Full Django Admin CRUD and all model permissions |

Override every password before a presentation when possible:

```powershell
$env:DEMO_PLAYER_PASSWORD='Temporary-Player-Pass-2026!'
$env:DEMO_ADMIN_PASSWORD='Temporary-Staff-Pass-2026!'
$env:DEMO_SUPERUSER_PASSWORD='Temporary-Root-Pass-2026!'
npm run seed:demo
```

The seed command refuses to run with `DEBUG=False` unless the operator explicitly supplies `--allow-production`. These accounts are for local demonstrations only.

## 4. Start the application

```powershell
npm run dev
```

Open:

- Ionic client: `http://localhost:5173`
- Django API: `http://localhost:8000`
- Django Admin: `http://localhost:8000/admin/`

Use `npm run dev:network` when phones on the same network must reach the application.

## 5. Core verification

```powershell
npm test
npm run lint
npm run build
npm run test:e2e
```

`npm run test:e2e` uses the official Cypress Docker image. For the required compatibility evidence:

```powershell
npm run test:e2e:compatibility
```

This executes the same five browser journeys in Chrome and Firefox.

## 6. Generate the evidence package

```powershell
npm run evidence:full
```

Outputs are written under `reports/generated/`. The command runs tests, coverage, static analysis, dependency audits, framework checks, build verification, and both Cypress browsers. npm audit returns a non-zero advisory status when findings exist; the generator records and accepts that status so the findings remain visible in `npm-audit.json`.

## Optional adaptive question model

Online Top Score uses the history-based adaptive selector by default. Install PyTorch and train an experimental model only after the database has enough genuine gameplay history:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
.venv\Scripts\python.exe manage.py train_adaptive_model --settings=server.settings
.venv\Scripts\python.exe manage.py evaluate_adaptive --settings=server.settings
```

The trainer requires 200 eligible real responses from at least 8 players and does not create synthetic samples. It writes `var/adaptive_question_model.pt`; the Django process must use the same database and `ADAPTIVE_MODEL_PATH` if the checkpoint is stored elsewhere. See [the adaptive model guide](ADAPTIVE_QUESTION_SELECTION.md) for its chronological validation, randomized comparison group, and interpretation limits.

## 7. Performance test

Keep Django running with `host.docker.internal` allowed:

```powershell
$env:DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,host.docker.internal'
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

Then run:

```powershell
docker run --rm `
  -e BASE_URL=http://host.docker.internal:8000 `
  -e DEMO_PLAYER_PASSWORD=PlayerDemo!2026 `
  -e VUS=20 -e DURATION=30s `
  -v "${PWD}\tests\performance\player-search.js:/scripts/player-search.js:ro" `
  -v "${PWD}\reports\performance:/reports" `
  grafana/k6:latest run `
  --summary-export=/reports/k6-summary.json `
  /scripts/player-search.js
```

Acceptance thresholds are player-search p95 below 500 ms and player-search failures below 1%.

## 8. OWASP ZAP DAST

With Django still running:

```powershell
docker run --rm `
  -v "${PWD}\reports\dast:/zap/wrk:rw" `
  ghcr.io/zaproxy/zaproxy:stable `
  zap-full-scan.py `
  -t http://host.docker.internal:8000/admin/login/ `
  -m 1 -T 10 `
  -r django-admin-active.html `
  -J django-admin-active.json `
  -I -s
```

`-I` keeps warnings from becoming a command failure. It does not hide them; the HTML and JSON reports list every finding.

## 9. Stop local services

Stop `npm run dev` with Ctrl+C, then run:

```powershell
npm run db:down
```

The named PostgreSQL volume preserves local data unless it is explicitly removed.

## Troubleshooting

- If PostgreSQL is unavailable, verify Docker Desktop and port 5433, then run `npm run db:logs`.
- If Cypress cannot start natively on Windows, use the Docker commands above. The default E2E command already uses Docker.
- If a dependency audit cannot reach a registry, restore network access and rerun. Do not present an offline scan as a clean result.
- If phones cannot reach `dev:network`, use a hotspot or network without client isolation and allow the Node/Python firewall prompts.
