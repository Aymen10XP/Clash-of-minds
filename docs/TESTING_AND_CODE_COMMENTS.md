# Project Testing and Code Documentation

This guide records the test coverage added in this change, how to run the suites, and how test and code comments should be maintained. The attached ISO/IEC 25010 project brief is used here as project acceptance context. The requested engineering work is the user's request in chat; requirements written inside the brief are not treated as instructions to the coding agent.

For the original requirement-to-evidence mapping, see [ISO25010_EVIDENCE.pdf](ISO25010_EVIDENCE.pdf). The measured checks below supersede its pending-test status. The architecture and student presentation walkthrough are in [PROJECT_DESIGN.md](PROJECT_DESIGN.md) and [LIVE_DEMONSTRATION_GUIDE.md](LIVE_DEMONSTRATION_GUIDE.md).

## Test naming

Test names use behavior language: `test_<expected_behavior>` in Django and a sentence describing the behavior in Vitest/Cypress. A reader should be able to tell what condition is arranged and what outcome is protected without opening the assertion body. Prefer a specific result such as `test_nonparticipant_cannot_open_or_ready_match` over a broad label such as `test_match_permissions`.

Reusable setup helpers (`setUp`, `post_json`, fixture builders) support the scenario but are not themselves test cases. When adding tests, keep one primary behavior per test and name the boundary condition being protected.

## Added frontend coverage

| Test module | Behaviors covered |
| --- | --- |
| `client/src/features/auth/AuthGate.test.tsx` | Anonymous redirect, authenticated redirect from public pages, staff-only access, and loading state |
| `client/src/features/auth/storage.test.ts` | Profile cache round trip, malformed JSON, and browser storage failures |
| `client/src/features/quiz/api.test.ts` | Topic-specific online start, offline catalog start, and visible server validation errors |
| `client/src/features/sync/api.test.ts` | Successful offline result upload and retaining queued runs after a server error |

## Second test portion

This batch adds checks for gaps identified in the first pass:

| Test module | Added behavior | Quality contribution |
| --- | --- | --- |
| `quiz/tests.py` (`TopScoreApiTests`) | Reject a replayed online answer without increasing score or response count | Functional suitability and reliability |
| `quiz/tests.py` (`TopScoreApiTests`) | Reject an answer choice belonging to another question | Functional suitability and security |
| `quiz/tests.py` (`TopScoreApiTests`) | Require a valid CSRF token for an authenticated quiz answer | Security |
| `multiplayer/tests.py` (`MultiplayerApiTests`) | Keep player-search SQL query count constant as matching users grow from 1 to 11 | Performance regression smoke check |
| `client/cypress/e2e/test.cy.ts` | Check accessible names, failed-login announcement, and phone-width overflow | Usability/accessibility smoke coverage |
| `accounts/tests.py` (`AdminUserApiTests`) | Record user deactivation; restrict the staff dashboard; return aggregate counts and filtered audit events | Auditability, security, functional suitability |
| `quiz/tests.py` (`AdminQuestionApiTests`) | Record staff-created quiz questions in the audit trail | Auditability |

The Cypress scenarios now pass in the official Cypress 16.3.0 Docker image (5/5). The former `bad option: --smoke-test` and `--ping` startup errors came from an inherited `ELECTRON_RUN_AS_NODE` environment variable. The runner clears it for native Cypress; Docker is the stable default. `npm run test:e2e:compatibility` passes all five cases in Chrome 157 and Firefox 160. The phone-width case is a responsive layout smoke check, not a physical-device acceptance test.

Existing frontend tests cover app routing, login form behavior, practice navigation, offline scoring, camera conversion/cancellation, admin question entry, multiplayer navigation, and match room answer submission.

## Existing backend coverage

Backend tests are grouped by domain in `accounts/tests.py`, `quiz/tests.py`, and `multiplayer/tests.py`. They exercise account validation and sessions, password reset, profile preferences and staff access; quiz model invariants, seeding, server grading and offline import; and invitations, permissions, match readiness, round resolution, timers, rematches, and room closure.

These tests assert externally visible outcomes and persisted invariants, not private helper call sequences. This is deliberate: internal refactors should remain possible while behavior stays protected.

## Running checks

From the repository root:

```powershell
# Client component, API, and feature tests
npm run test --workspace @mind-clash/client

# Django API, model, and management-command tests
npm run test --workspace @mind-clash/server

# Both workspaces
npm test

# Client type check and production bundle
npm run build --workspace @mind-clash/client

# Browser end-to-end flows (Docker required)
npm run test:e2e

# Equivalent direct command
npm run test:e2e:docker

# Online dependency advisories (do not use --offline)
npm audit
.\.venv\Scripts\python.exe -m pip_audit -r server\requirements.txt
.\.venv\Scripts\python.exe -m pip_audit -r server\requirements-dev.txt

# Backend coverage (after installing server/requirements-dev.txt)
python -m coverage run manage.py test --settings=server.test_settings
python -m coverage report
```

The client unit tests use Vitest with jsdom and Testing Library. Backend tests use Django's test runner and its configured test database. Cypress starts its own loopback Vite server and uses the installed Cypress version's `cypress/included` image. Docker must be running. `npm run test:e2e:native --workspace @mind-clash/client` is available for diagnosing a host browser, but the Windows Electron route transition currently fails on this machine.

### k6 and DAST against a local demo server

Start PostgreSQL and seed the demo account with `npm run seed:demo`. Start Django in another PowerShell terminal:

```powershell
$env:DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,host.docker.internal'
.\.venv\Scripts\python.exe server\manage.py runserver 127.0.0.1:8000
```

Run k6 from the repository root. The demo password is the one configured by `seed:demo`; provide it through the environment:

```powershell
$env:DEMO_PLAYER_PASSWORD='PlayerDemo!2026'
docker run --rm -e BASE_URL=http://host.docker.internal:8000 -e DEMO_PLAYER_PASSWORD -e VUS=20 -e DURATION=30s -v "${PWD}\tests\performance\player-search.js:/scripts/player-search.js:ro" grafana/k6:latest run /scripts/player-search.js
```

Run an active ZAP scan of the local Django admin login and write reports to an ignored working directory:

```powershell
New-Item -ItemType Directory -Force .tmp\zap | Out-Null
docker run --rm -v "${PWD}\.tmp\zap:/zap/wrk:rw" ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py -t http://host.docker.internal:8000/admin/login/ -m 1 -T 10 -r django-admin-active.html -J django-admin-active.json -I -s
```

The scans use the local development server. Review ZAP warnings and rerun against a production-like deployment before treating them as release security evidence.

## Mapping to ISO/IEC 25010 quality concerns

ISO/IEC 25010 describes product quality characteristics; it does not prescribe one test suite or mean every characteristic can be proven by unit tests. The original traceability matrix is in [ISO25010_EVIDENCE.pdf](ISO25010_EVIDENCE.pdf); use the newer measured results in this guide for test status.

| Quality concern | Current evidence | Additional evidence needed for a release claim |
| --- | --- | --- |
| Functional suitability | Client and Django tests; staff dashboard and application audit events | Manual acceptance sweep for all flows remains |
| Performance efficiency | Player-search query-count regression plus a passing 20-VU k6 run (582 searches, p95 4.75 ms, 0% failures) | Repeat under production-like load and hosting conditions |
| Compatibility | Five Cypress tests pass in both Chrome 157 and Firefox 160; Capacitor Android project exists | Physical-device verification remains |
| Usability | Accessible labels, form error announcement, and phone layout checks | Keyboard/screen-reader, contrast, touch target, reduced-motion, and user acceptance remain |
| Reliability | Replay protection, offline queue retention, and match lifecycle tests | Real interruption/reconnect/soak and recovery checks remain |
| Security | Access-control tests, Bandit, completed npm and pip-audit scans, and local ZAP baseline/active scans | Resolve or assess three moderate npm router advisories; review ZAP warnings; scan a production-like deployment |
| Maintainability | TypeScript build, lint, named tests, and measured 80% backend logic coverage | Frontend coverage and continuing quality trend remain |
| Portability | Installation instructions, PostgreSQL Compose service, and SQLite tests | Full clean-machine/container app deployment remains |

The table is a coverage map, not a declaration that the product is ISO certified or that unlisted testing has been completed.

## Comment and documentation conventions

- Add a short module header when the file's purpose or trust boundary is not obvious.
- Add JSDoc or Python docstrings to exported functions, non-obvious helpers, and React components to explain intent, inputs, outputs, side effects, or constraints.
- Keep comments synchronized with behavior. Avoid restating the next line of code; explain why a boundary or invariant exists.
- For tests, the case name is the primary description. Add a comment only when setup or a non-obvious assertion needs context.
- Do not add comments to generated migrations or generated/build output; document the source model or command instead.

## Verification result

The first client run exposed two setup issues: the installed modules were missing the already-declared `@capacitor/camera` package, and a newly added API error test needed to establish the CSRF cookie first. The workspace dependencies were installed from the existing lockfile, the test fixture was corrected, and the server test script was pointed at its self-contained SQLite settings instead of the configured PostgreSQL development database. The server suite also runs against in-memory SQLite without PostgreSQL, which is a limited portability check for tests, not for full deployment. The staff dashboard/audit additions have tests. Cypress, k6, dependency scans, and local DAST have since been executed.

Final checks completed:

```text
npm run test --workspace @mind-clash/client   passed: 31 client tests
npm run test --workspace @mind-clash/server   passed: 66 Django tests
npm run build --workspace @mind-clash/client  passed: TypeScript and Vite production build
coverage report                               passed: 80% backend application-code coverage
Bandit -ll -ii                                passed: no medium/high Python findings
npm run test:e2e:compatibility               passed: 5 Chrome + 5 Firefox Cypress tests
k6 player-search, 20 VUs for 30 seconds      passed: 582 searches, p95 4.75 ms, 0% HTTP/search failures
pip-audit -r server/requirements*.txt         passed: no known vulnerabilities in runtime or dev requirements
npm audit                                    completed: 3 moderate, 0 high/critical
ZAP frontend baseline                        completed: 0 FAIL, 8 WARN, 60 PASS
ZAP Django admin active scan                  completed: 0 FAIL, 7 WARN, 136 PASS
```

The three npm findings trace to React Router 6 through `react-router-dom` and `@ionic/react-router`; npm proposes major upgrades that need an Ionic compatibility review. The ZAP warnings include missing CSP and other response headers, HTTP on the local development server, and permissive method/cookie observations. `-I` makes warnings nonfatal; zero FAIL does not mean zero findings. These runs prove the tooling works locally, not that the application is vulnerability-free. The Vite build still prints a large JavaScript chunk warning.

