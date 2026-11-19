# Clash of Minds - Requirements Traceability Matrix

Execution date for the recorded evidence: 19 November 2026. Evidence paths are relative to the repository root.

## Functional requirements

| ID | Requirement from the brief | Implemented evidence | Test or tool | Recorded result |
| --- | --- | --- | --- | --- |
| F-01 | Authentication and at least three differentiated profiles | Django sessions; `demo_player`, `demo_admin`, and `demo_superuser`; server-side staff/superuser checks | Django account/admin tests; `seed_demo` test | Three profiles created idempotently; backend suite passed |
| F-02 | At least four related business entities with complete CRUD | `User` M-N `Topic`; `Question` N-1 `Topic`; `AnswerChoice` N-1 `Question`; full CRUD in Django Admin; additional game entities | Django model tests and Admin registration inspection | More than four related entities available; superuser CRUD enabled |
| F-03 | Status workflow with transition rules | Invitation: pending to accepted/declined/cancelled; match: waiting to active to completed/cancelled; quiz run: active to finished/abandoned | `multiplayer/tests.py`, `quiz/tests.py` | Invalid, repeated, unauthorized, and late transitions rejected; backend suite passed |
| F-04 | Dashboard with aggregate indicators and filters | Staff dashboard shows active users/topics/questions, matches by status, and audit-action filter | Django `AdminUserApiTests`; React `AdminConsole.test.tsx` | API and UI tests passed |
| F-05 | Search/filter on a high-volume entity | Indexed player search by username; bounded results; audit-action filtering | Django query-count regression; k6 | Query count remains bounded; 582 searches, 4.75 ms p95, 0% failures |
| F-06 | Audit log for sensitive actions | Append-only `AuditEvent` stores actor, action, target, details, timestamp | User-deactivation and question-creation tests | Events created and dashboard filter tested |
| F-07 | At least five explicit business rules | Unique account email; valid active-question structure; one response per run question; run status consistency; no self-invite; one pending invitation; participant-only match access; one answer per player/round; server-owned scoring | Django unit/integration tests | 66 backend tests passed |

## ISO/IEC 25010 requirements

| ID | Characteristic | Concrete requirement | Test/tool | Result and evidence |
| --- | --- | --- | --- | --- |
| Q-01 | Functional suitability | Required workflows return correct state and errors | Django TestCase, Vitest, Cypress | 66 backend, 31 client, and 10 cross-browser E2E executions passed; `reports/generated/tests/` |
| Q-02 | Performance efficiency | Player search p95 below 500 ms at 20 concurrent users; failures below 1% | k6 | 4.75 ms p95, 0% search and HTTP failures, 582 iterations; `reports/performance/k6-summary.json` |
| Q-03 | Compatibility | Same critical journeys work in at least two browsers | Cypress 16.3.0 in Chrome 157 and Firefox 160 | 5/5 in each browser; `reports/generated/tests/cypress-compatibility.log` |
| Q-04 | Usability | Named controls, labelled form, announced errors, phone-width layout | Cypress, Testing Library | All checks passed in both browsers; manual acceptance remains recommended |
| Q-05 | Reliability | Retries and replay must not duplicate or corrupt persisted game data | Django transaction/idempotency tests and frontend offline-queue tests | Replay, duplicate sync, failure retention, timers, forfeit, rematch and deletion tests passed |
| Q-06 | Security | Role checks, CSRF, known-code/dependency and runtime web scan evidence | Access tests, Bandit, ESLint, npm audit, pip-audit, ZAP | No Bandit medium/high findings; Python audits clean; npm has 3 moderate router advisories; ZAP 0 FAIL and 7 WARN |
| Q-07 | Maintainability | Layered code, lint/build checks, measured coverage | ESLint, TypeScript/Vite, coverage.py, Django checks | Lint/build/checks passed; 80% backend application-code coverage |
| Q-08 | Portability | Reproducible installation and test execution on another machine | Docker Compose, seed script, evidence generator, installation guide | PostgreSQL container/seed/tests executed; documented third-party procedure provided |

## Test-layer coverage required by section 7

| Layer | Repository implementation | Generated evidence |
| --- | --- | --- |
| Unit tests | Django model/business rules; Vitest feature utilities/components | Backend and client logs, JUnit XML |
| Integration tests | Django API plus test database interactions | Backend test log and coverage XML |
| API tests | HTTP status, payload, CSRF, authorization and persistence assertions | Backend test log |
| Functional/E2E | Cypress navigation, login error, accessibility and viewport journeys | Chrome/Firefox Cypress log |
| Performance | Authenticated player-search scenario | k6 JSON summary |
| Reliability | Offline queue retention, replay/idempotency and match lifecycle tests | Client/backend test logs |
| SAST | Bandit for Python; ESLint for TypeScript | Bandit and ESLint JSON |
| SCA | pip-audit and npm audit | Runtime/dev Python JSON and npm JSON |
| DAST | ZAP baseline and full active scan | HTML and JSON under `reports/dast/` |
| Maintainability | Coverage, lint, build, framework and migration checks | Coverage XML/text, ESLint JSON, build/check logs |
| Compatibility | Cypress Chrome and Firefox | Cypress compatibility log |
| Portability | Docker Compose, seeded PostgreSQL, documented scripts | Installation guide and successful evidence summary |

## Evidence integrity

No unavailable result is represented as passing. The three moderate npm findings and seven ZAP warnings remain in the committed machine-readable reports. Measurements describe the local test environment and must not be interpreted as a production SLA or formal ISO certification.
