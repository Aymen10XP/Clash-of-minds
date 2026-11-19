# Clash of Minds - ISO/IEC 25010 Quality Evaluation

## Report status

- Evaluation date: 19 November 2026
- Target: local development build on Windows 11, Docker Desktop, PostgreSQL 17
- Scope: the eight product-quality characteristics requested by the student brief
- Claim: evidence-based academic evaluation; no formal ISO certification is claimed

## Executive summary

Clash of Minds satisfies the demonstrable requirements in the provided brief. The repository contains a full Ionic/React client, Django API, relational PostgreSQL data model, three permission profiles, model CRUD through Django Admin, status workflows, filtered dashboard, search, audit logging, and automated tests across the requested layers.

The recorded core evidence run completed successfully. The remaining known security work is visible rather than suppressed: npm reports three moderate React Router advisories and ZAP reports seven warnings on the local HTTP development server.

## 6.1 Functional suitability

**Requirement.** Authentication/roles, related CRUD entities, status workflow, dashboard, search, audit trail, and at least five explicit business rules must work correctly.

**Evidence.** Django executed 66 model/API tests; Vitest executed 31 client tests; Cypress executed five critical journeys in Chrome and the same five in Firefox. The data model has twelve application entities. Full CRUD for `User`, `Topic`, `Question`, `AnswerChoice`, and the game records is available to the superuser in Django Admin. The custom staff console exposes the daily dashboard, question creation, audit filtering, and protected user deactivation.

**Result.** Passed for the implemented scope. Story and ranked modes are visible placeholders and are not requirements of the professor's brief.

## 6.2 Performance efficiency

**Requirement.** Response time below 500 ms under 20 simultaneous users.

**Method.** k6 authenticated each virtual user, retained its session, and repeatedly queried player search for 30 seconds. Session bootstrap was staggered so the run measured the endpoint rather than the development server's small connection-accept queue.

**Result.** Passed: 20 VUs, 582 search iterations, 1,184 checks, 100% checks passed, 0% HTTP/search failures, player-search p95 4.75 ms, HTTP p95 5.32 ms. See `reports/performance/k6-summary.json`.

**Limit.** This local result demonstrates the required test and threshold. It is not production capacity evidence.

## 6.3 Compatibility

**Requirement.** At least two browsers or coexistence with an external system.

**Method.** Cypress 16.3.0 ran the same E2E specification in Docker Chrome 157 and Firefox 160.

**Result.** Passed: five tests in Chrome and five in Firefox. The tests cover authenticated navigation, Ionic shadow-DOM accessible names, route transitions, login error announcements, and a mobile viewport overflow check. See `reports/generated/tests/cypress-compatibility.log`.

## 6.4 Usability

**Requirement.** Validate an understandable user journey and basic accessibility.

**Evidence.** Browser tests verify named game navigation/account controls, labelled login inputs, an announced authentication error, and no horizontal overflow at an iPhone 6 viewport. React component tests cover login and major menu paths.

**Result.** Automated baseline passed in both browsers.

**Limit.** A human screen-reader, contrast, keyboard, and user-acceptance session would strengthen a production usability claim.

## 6.5 Reliability

**Requirement.** Correct recovery and no data loss/corruption during errors or repeated operations.

**Evidence.** Tests cover replay rejection, offline-sync idempotency, retention of pending offline runs after server failure, transaction-protected match transitions, authorization, round deadlines, draws, forfeits, rematches, and final room deletion. Database constraints enforce one active round and one answer per participant/round.

**Result.** Passed for the tested failure and repetition scenarios.

## 6.6 Security

**Requirement.** Strong authentication, role checks, and evidence against common code, dependency, and runtime web weaknesses.

**Evidence and result.**

| Control | Result |
| --- | --- |
| Authentication and access control | Session, CSRF, anonymous/player/staff/superuser boundaries covered by API tests |
| Bandit SAST | 0 medium/high findings; report contains no execution errors |
| ESLint static analysis | Completed with zero lint errors |
| Python SCA | No known vulnerabilities in runtime or development requirements |
| npm SCA | 3 moderate, 0 high, 0 critical findings, all in React Router/Ionic routing chain |
| ZAP active DAST | 0 FAIL, 7 WARN, 136 PASS against local Django admin login |

The ZAP warnings cover CSP/permissions/resource headers, local HTTP, a PUT-method observation, a cookie flag observation, and server version disclosure. The scan targets Django `runserver`, so HTTP and server-banner observations require production-server verification. Reports are under `reports/generated/security/` and `reports/dast/`.

**Result.** The required security layers execute successfully and findings are disclosed. The moderate npm advisories and ZAP warnings remain documented risk items rather than being labelled clean.

## 6.7 Maintainability

**Requirement.** Structured code, controlled complexity, and measured test coverage.

**Evidence.** The repository separates account, quiz, and multiplayer Django domains; React separates routes, pages, features, and reusable components. ESLint, TypeScript compilation, Vite production build, Django checks, migration drift, and coverage all ran in the evidence generator.

**Result.** Passed: build/lint/checks succeed and backend application-code coverage is 80% (1,019 of 1,207 statements covered, with branch measurement enabled). The build reports a large bundle warning, which is a future optimization.

## 6.8 Portability

**Requirement.** Reproducible third-party installation through scripts or containers.

**Evidence.** Docker Compose supplies PostgreSQL with a health check and persistent volume. `npm run seed:demo` starts the database, migrates schema, seeds content, and creates the three demo roles. `npm run evidence:full` creates the repeatable quality report package. The installation guide provides exact Windows commands.

**Result.** Passed for the documented Windows/Docker environment. Android packaging and production deployment are outside the professor's minimum portability check.

## Findings requiring follow-up

1. Review a compatible Ionic/React Router upgrade when fixed versions are supported; npm currently proposes breaking major versions.
2. Apply security headers and TLS in the production reverse proxy, then rerun ZAP against that deployment.
3. Add a human accessibility/acceptance record if the professor requests user-test evidence.
4. Split the large frontend bundle before a production optimization claim.

## Evidence index

- `reports/generated/summary.json`: timestamped command/exit-code manifest
- `reports/generated/tests/`: unit, integration and cross-browser results
- `reports/generated/coverage/`: measured backend coverage
- `reports/generated/security/`: SAST, lint and dependency reports
- `reports/performance/k6-summary.json`: load-test metrics
- `reports/dast/`: ZAP HTML and JSON reports
- `docs/TRACEABILITY_MATRIX.md`: requirement-to-test-to-tool-to-result mapping
