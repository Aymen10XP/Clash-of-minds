# Clash of Minds - Concise Live Demonstration Guide

Use this script for a 12-15 minute defense. Keep one terminal for the app, one for tests, Chrome for the player/staff UI, Firefox for the second player, and the reports folder open in the editor.

## Prepare tonight

```powershell
npm install
.\.venv\Scripts\python.exe -m pip install -r server\requirements-dev.txt
npm run seed:demo
npm run evidence:full
```

Confirm Docker Desktop is running and these files open correctly:

- `docs/FINAL_PROJECT_REPORT.md`
- `docs/TRACEABILITY_MATRIX.md`
- `docs/ISO25010_COMPLIANCE_REPORT.md`
- `reports/dast/django-admin-active.html`
- `reports/generated/coverage/backend-coverage.txt`

Demo credentials are local only:

| Profile | Username | Default password |
| --- | --- | --- |
| Player | `demo_player` | `PlayerDemo!2026` |
| Staff operator | `demo_admin` | `AdminDemo!2026` |
| Superuser | `demo_superuser` | `SuperDemo!2026` |

Run `npm run seed:demo` again tomorrow if anything was changed during rehearsal. It is idempotent.

## Start five minutes before the defense

```powershell
npm run dev
```

Open:

- Chrome: `http://localhost:5173`
- Firefox/private window: `http://localhost:5173`
- Django Admin: `http://localhost:8000/admin/`

Keep the root of the repository visible in the editor so every claim can be tied to a file or generated report.

## Presentation script

### 1. Introduce the product and architecture - 1 minute

Say:

> Clash of Minds is an Ionic/React trivia client backed by Django and PostgreSQL. Django owns permissions, scoring and multiplayer state; the client owns interaction and presentation. We evaluated the implemented application against all eight ISO/IEC 25010 quality characteristics requested in the brief.

Show `docs/FINAL_PROJECT_REPORT.md`, sections 2 and 3. Point to the client, three Django domains, and PostgreSQL. Mention that the model contains twelve application entities, well above the four-entity minimum.

### 2. Prove the functional minimum - 3 minutes

Sign in as `demo_player`.

1. Open VS Bot and start a practice game.
2. Explain that Django verifies the selected choice and official score.
3. Open Top Score and point out the selection note. It identifies history-based adaptive practice, a trained experimental model, or a randomized comparison run. The neural label appears only after a real-data checkpoint has been trained and installed. See [Adaptive Question Selection](ADAPTIVE_QUESTION_SELECTION.md) for the data threshold and evaluation limits.
4. Open Multiplayer and show player search/invitations.
5. If both browser sessions are ready, invite the Firefox player, accept, ready both players, and answer one round.

Say:

> The status workflows are invitation pending/accepted/declined/cancelled, match waiting/active/completed, round active/resolved, and quiz run active/finished/abandoned. Invalid or repeated transitions are rejected by the server.

If the two-player live flow risks taking too long, show the screen and then point to the passing backend workflow tests instead.

### 3. Prove three profiles, CRUD, dashboard and audit - 3 minutes

Sign out and sign in as `demo_admin`.

1. Open Admin Console.
2. Show active user/topic/question indicators and matches grouped by status.
3. Filter the audit list.
4. Create a disposable question with four choices and one correct answer.
5. Point to the new `quiz.question.created` audit event.

Then open Django Admin as `demo_superuser` and show the model list. Open Topics or Questions to demonstrate complete create/read/update/delete administration.

Say:

> The three profiles are player, staff operator, and superuser. Rights are enforced in Django. The superuser has complete model CRUD; the staff operator has the safer daily console; the player cannot access either.

Do not delete seeded records during the live defense.

### 4. Run two test layers live - 3 minutes

In the test terminal run:

```powershell
npm run test --workspace @mind-clash/client
npm run test --workspace @mind-clash/server
```

Expected current totals are 31 client tests and 66 backend tests.

Explain:

> The first layer checks React components and client API behavior in jsdom. The second sends requests through Django and verifies database results, authorization, status transitions, replay protection and constraints.

If time permits, run one real-browser layer:

```powershell
npm run test:e2e
```

Mention that the committed compatibility log contains the same five tests passing in both Chrome and Firefox.

### 5. Present the ISO 25010 evidence - 3 minutes

Open `docs/ISO25010_COMPLIANCE_REPORT.md` and summarize this table verbally:

| Characteristic | One sentence to say |
| --- | --- |
| Functional suitability | Required workflows passed 66 backend, 31 client, and cross-browser E2E tests. |
| Performance | k6 measured 4.75 ms player-search p95 at 20 users, below 500 ms, with 0% failures. |
| Compatibility | Five Cypress journeys passed in Chrome 157 and Firefox 160. |
| Usability | Labels, error announcement and phone-width layout passed browser checks. |
| Reliability | Replay, offline retry/idempotency, timer, forfeit, rematch and deletion cases are tested. |
| Security | Role/CSRF tests, Bandit, dependency audits and ZAP ran; findings remain disclosed. |
| Maintainability | Lint/build/checks passed and backend application coverage is 80%. |
| Portability | Docker Compose, seeded data and one evidence command reproduce the environment. |

Open `docs/TRACEABILITY_MATRIX.md` and say:

> This is the required traceability chain: requirement, implementation, test/tool, actual result and evidence path.

### 6. Explain findings honestly - 1 minute

Show the ZAP HTML report and npm audit JSON.

Say:

> We do not claim formal ISO certification or zero vulnerabilities. Python audits and medium/high Bandit checks are clean. npm reports three moderate router advisories. ZAP reports zero failing alerts and seven warnings on the local HTTP development server. These are documented follow-up items, not hidden results.

Also mention the large frontend bundle warning and that Story/Ranked are optional placeholders outside the professor's minimum requirements.

## How to explain each requested document

| Document | What to tell the professor |
| --- | --- |
| Final project report | Architecture, entities, roles, workflows, technology choices and delivery inventory |
| Traceability matrix | Every brief requirement links to implementation, tool/test, result and evidence |
| ISO compliance report | One concrete requirement and executed proof for each of the eight characteristics |
| Installation guide | A third party can install, seed, run, test and stop the project from exact commands |
| `reports/` | Raw generated evidence: JUnit, coverage, logs, security JSON, k6 and ZAP HTML/JSON |

## Backup plan

- App startup failure: show `reports/generated/summary.json`, the reports, and run the self-contained tests.
- Database failure: run `npm run db:up`, then `npm run seed:demo`.
- Second-browser flow failure: show the Chrome/Firefox Cypress log and backend multiplayer tests.
- Internet failure: all committed evidence remains local; do not rerun registry-dependent audits.
- Short time: demonstrate architecture, one player flow, staff/audit, two test commands, and the ISO table.

> Every shown result comes from an executable test or generated report; warnings stay explicit and no evidence is invented.
