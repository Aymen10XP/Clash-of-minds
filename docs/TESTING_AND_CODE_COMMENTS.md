# Project Testing and Code Documentation

This guide records the test coverage added in this change, how to run the suites, and how test and code comments should be maintained. The attached ISO/IEC 25010 project brief is used here as project acceptance context. The requested engineering work is the user's request in chat; requirements written inside the brief are not treated as instructions to the coding agent.

For current requirement-to-evidence mapping, measured results, and remaining external checks, see [ISO25010_EVIDENCE.md](ISO25010_EVIDENCE.md). The architecture and student presentation walkthrough are in [PROJECT_DESIGN.md](PROJECT_DESIGN.md) and [LIVE_DEMONSTRATION_GUIDE.md](LIVE_DEMONSTRATION_GUIDE.md).

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

The Cypress scenarios are authored but could not be executed in this environment: Cypress 13.17.0 exits at startup with `bad option: --smoke-test` and a `--ping` startup error. Treat these browser checks as pending verification until Cypress can start on a supported local setup. The phone-width case is a responsive layout smoke check; it does not prove multi-browser compatibility.

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

# Browser end-to-end flows
npm run test:e2e

# Backend coverage (after installing server/requirements-dev.txt)
python -m coverage run manage.py test --settings=server.test_settings
python -m coverage report
```

The client unit tests use Vitest with jsdom and Testing Library. Backend tests use Django's test runner and its configured test database. Cypress specs define browser-level route interactions but are not currently executable in the provided environment. A failure at tool startup (for example, a missing installed package) should be reported separately from a failing assertion.

## Mapping to ISO/IEC 25010 quality concerns

ISO/IEC 25010 describes product quality characteristics; it does not prescribe one test suite or mean every characteristic can be proven by unit tests. The brief asks for concrete test evidence and a quality report. The current detailed traceability matrix, actual results, and environment-dependent work are maintained in [ISO25010_EVIDENCE.md](ISO25010_EVIDENCE.md).

| Quality concern | Current evidence | Additional evidence needed for a release claim |
| --- | --- | --- |
| Functional suitability | Client and Django tests; staff dashboard and application audit events | Manual acceptance sweep for all flows remains |
| Performance efficiency | Player-search query-count regression plus k6 scenario with a p95 threshold | k6 execution and measured output remain pending |
| Compatibility | Cypress browser tests and Capacitor Android project | Cypress execution and two-browser/device verification remain pending |
| Usability | Accessible labels, form error announcement, and phone layout checks | Keyboard/screen-reader, contrast, touch target, reduced-motion, and user acceptance remain |
| Reliability | Replay protection, offline queue retention, and match lifecycle tests | Real interruption/reconnect/soak and recovery checks remain |
| Security | Access-control tests and Bandit run | Dependency scans and DAST remain pending |
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

The first client run exposed two setup issues: the installed modules were missing the already-declared `@capacitor/camera` package, and a newly added API error test needed to establish the CSRF cookie first. The workspace dependencies were installed from the existing lockfile, the test fixture was corrected, and the server test script was pointed at its self-contained SQLite settings instead of the configured PostgreSQL development database. The server suite also runs against in-memory SQLite without PostgreSQL, which is a limited portability check for tests, not for full deployment. The staff dashboard/audit additions have tests. Cypress still cannot start here, as recorded in the quality evidence report.

Final checks completed:

```text
npm run test --workspace @mind-clash/client   passed: 31 client tests
npm run test --workspace @mind-clash/server   passed: 66 Django tests
npm run build --workspace @mind-clash/client  passed: TypeScript and Vite production build
coverage report                               passed: 80% backend application-code coverage
Bandit -ll -ii                                passed: no medium/high Python findings
```

The Vite build still prints Ionic stylesheet `host-context` minifier warnings and a large JavaScript chunk warning. They did not fail the build and are separate from the test additions. Dependency scanning, DAST, k6 execution, and browser/device checks are not yet recorded; see [ISO25010_EVIDENCE.md](ISO25010_EVIDENCE.md) for the exact status and commands.

