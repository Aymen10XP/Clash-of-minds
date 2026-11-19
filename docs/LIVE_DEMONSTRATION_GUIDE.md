# Mind Clash: Live Demonstration Guide

Use this as a 10–15 minute student presentation script. It gives you a repeatable local setup, a short product tour, two test layers to run live, and the evidence to show. Adjust the timing if your instructor assigns a different limit.

## Before the presentation

Have Node.js/npm, Python, Docker Desktop, Git, and the project dependencies installed. Make sure Docker is running. The project uses PostgreSQL for the local demo; the automated Django tests use SQLite and do not need a database service.

From the repository root in PowerShell:

```powershell
# Only needed if the local environment file has not been created yet
Copy-Item server/.env.example server/.env

npm install
.venv\Scripts\python.exe -m pip install -r server/requirements.txt

# Choose temporary demo passwords for this presentation. Do not reuse personal passwords.
$env:DEMO_PLAYER_PASSWORD = 'Choose-A-Temporary-Player-Pass-2026!'
$env:DEMO_ADMIN_PASSWORD = 'Choose-A-Temporary-Staff-Pass-2026!'
npm run seed:demo
```

The seed command starts the PostgreSQL service, applies migrations, creates/upgrades `demo_player` and `demo_admin`, and loads quiz questions. The accounts have different access: the player is a normal account; the admin account is staff but not a superuser. If the instructor needs to see a third, distinct permission level, create a local superuser separately:

```powershell
.venv\Scripts\python.exe manage.py createsuperuser
```

Keep the passwords private and use only this local demo database. Do not use the seed accounts on a public deployment.

## Start the application

From the repository root:

```powershell
npm run dev
```

Open `http://localhost:5173`. The Vite development server proxies `/api` requests to Django at `http://127.0.0.1:8000`. Keep the terminal visible so you can show service startup and API output.

If database startup fails, check Docker Desktop, `server/.env`, and port 5433. If the frontend cannot reach the API, check the Vite/Django output and confirm both dev tasks are running.

## Presentation flow

### 1. Explain the problem and architecture (1 minute)

Say: “Mind Clash is a trivia game. The Ionic React app handles navigation and interaction; Django validates answers and owns account permissions, quiz scoring, and multiplayer state. PostgreSQL stores the relational data.”

Show [PROJECT_DESIGN.md](PROJECT_DESIGN.md) for the model relationships, role boundaries, and technology choices. Keep the explanation tied to what is implemented in this repository.

### 2. Demonstrate the player experience (2 minutes)

1. Sign in as `demo_player` with the temporary password you configured.
2. Show the game-mode navigation and its accessible labels.
3. Open **VS Bot**, choose a practice mode, and answer a question. Explain that score validation is performed by the backend for online play.
4. Show the multiplayer screens if time allows.

For a full two-player invitation demonstration, open a second browser profile/private window, register a temporary second player, then use **Multiplayer → Friendly Match** in both profiles to search, invite, accept, and enter the match room. Registration requires unique email and username values. Keep both windows visible during the round.

### 3. Demonstrate staff permissions, dashboard, and audit trail (2–3 minutes)

1. Sign out and sign in as `demo_admin`.
2. Open **Admin Console**. Point out the aggregate player/topic/question/match indicators and the audit-action filter.
3. Add a disposable quiz question with four distinct answers and select its correct answer. Confirm the success message and the new `quiz.question.created` audit event.
4. If desired, create a disposable player account and deactivate it to show the `accounts.user.deactivated` audit event. Do not deactivate the seeded demo account you still need.
5. Sign in as a normal player and show that the staff console is unavailable. Explain that the API also checks staff permissions; hiding a button is not the security boundary.
6. If you created a superuser, show `/admin/` separately and explain its broader Django permissions. Avoid editing/deleting data live unless you have time to restore it.

The dashboard API is `GET /api/auth/admin/dashboard/`; add `?action=quiz.question.created` to filter its audit event list.

### 4. Demonstrate two test layers (3–4 minutes)

Keep the app demo terminal running. In a second PowerShell terminal at the repository root, run the frontend component/API suite:

```powershell
npm run test --workspace @mind-clash/client
```

Then run the backend API/model integration suite:

```powershell
npm run test --workspace @mind-clash/server
```

The client suite should report **31 tests** and the backend suite **66 tests** for the state recorded in [ISO25010_EVIDENCE.md](ISO25010_EVIDENCE.md). Counts may change as tests are added. Highlight a few readable names, such as replay rejection, cross-question choice rejection, staff-only dashboard access, and player-search query-count stability.

Explain the layers simply: the first suite checks frontend behavior in a simulated browser; the second sends requests through Django and checks database outcomes. These are not the Cypress real-browser suite.

### 5. State the quality evidence and limits (1 minute)

Show [ISO25010_EVIDENCE.md](ISO25010_EVIDENCE.md). Report only the measurements recorded there: 80% backend application-code coverage with the stated exclusions, passing build/lint/tests, and Bandit results. Tell the audience that load testing, dependency scans, DAST, cross-browser/device execution, and user accessibility acceptance still need results from a suitable environment. This honesty follows the brief’s rule against claiming unrun tests.

## Optional checks to prepare evidence before the presentation

### Backend coverage report

After installing `server/requirements-dev.txt`, run:

```powershell
python -m coverage run manage.py test --settings=server.test_settings
python -m coverage report
python -m coverage html
```

Open `htmlcov/index.html`. The checked-in `.coveragerc` excludes test files, migrations, admin modules, app setup, and URL wiring from the percentage.

### SAST and dependency scanning

```powershell
python -m bandit -r accounts quiz multiplayer server -ll -ii
python -m pip_audit -r server/requirements.txt --cache-dir .tool-cache/pip-audit
npm audit --omit=dev --audit-level=high
```

Dependency scans need access to package advisory registries. Save their real outputs and list any unresolved findings; never present a failed network request as a clean scan.

### Performance run

Install k6 and start the local app with seeded data. In a separate PowerShell window:

```powershell
$env:DEMO_PLAYER_PASSWORD = 'the-temporary-demo-player-password'
$env:BASE_URL = 'http://127.0.0.1:8000'
$env:VUS = '20'
$env:DURATION = '1m'
k6 run tests/performance/player-search.js
```

The script checks player-search p95 below 500 ms and failures below 1%. Record the machine, database, seed size, and actual k6 output. A local development result is not a production capacity guarantee.

## Troubleshooting and backup plan

- **Cypress startup problem:** the recorded workstation error is an installed Cypress binary rejecting `--smoke-test` and `--ping`. On a machine with network access, try `npm exec --workspace @mind-clash/client -- cypress install --force`, then rerun `npm run test:e2e --workspace @mind-clash/client`. If startup still fails, state that the E2E spec is authored but could not run, then show the passing client and Django suites. Do not call them browser E2E tests.
- **Database/demo data problem:** restart PostgreSQL with `npm run db:up`, check `.env`, and rerun `npm run seed:demo`. Avoid running demo seed against production.
- **No second account:** skip the invitation flow; show VS Bot and the backend multiplayer API tests instead.
- **Time is short:** keep the order architecture → player flow → staff dashboard/audit → two test suites → honest limitations.

## Evidence to save after the live run

- A screenshot of the player experience and staff dashboard (hide email addresses or other personal data).
- Terminal output for both test commands, lint/build, and any scan actually completed.
- Test/device/browser versions and the result of each manual check.
- Any defect found, its impact, and whether it was fixed or remains open.

Do not label the project “ISO certified.” The deliverable is a documented quality evaluation against the student brief, supported by reproducible evidence.
