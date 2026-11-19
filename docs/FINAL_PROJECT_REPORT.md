# Clash of Minds - Final Design and Delivery Report

## 1. Project overview

Clash of Minds is a trivia application with authenticated player profiles, timed practice, offline play and synchronization, friendly two-player matches, and web administration. The system uses an Ionic/React client, a Django API, and PostgreSQL.

The project was evaluated against the professor's ISO/IEC 25010 brief. This report describes the implemented system; the traceability and compliance reports contain the measured proof.

## 2. Architecture

```text
Ionic + React + Capacitor client
  - session restoration and route guards
  - practice/offline queue/multiplayer/staff console
  - HTTP JSON requests with session cookie and CSRF token
                      |
                      v
Django application
  - accounts: authentication, profiles, roles, audit, dashboard
  - quiz: topics, questions, choices, runs, responses, offline sync
  - multiplayer: invitations, matches, participants, rounds, answers
  - Django Admin: complete CRUD for registered models
                      |
                      v
PostgreSQL 17 through Docker Compose
  - relational constraints, indexes, transactions, persistent volume
```

The automated Django suite uses isolated in-memory SQLite test settings for speed. Local demonstration and performance/DAST evidence use the PostgreSQL development environment.

## 3. Main data model

| Entity | Main relations and responsibility |
| --- | --- |
| `accounts.User` | Identity; M-N favorite topics; player/staff/superuser permissions |
| `accounts.AuditEvent` | N-1 optional actor; sensitive action, target, details and timestamp |
| `quiz.Topic` | 1-N questions; M-N favorite users |
| `quiz.Question` | N-1 topic; 1-N choices; draft/active publishing state |
| `quiz.AnswerChoice` | N-1 question; constrained position and correctness |
| `quiz.TopScoreRun` | N-1 user/topic/current question; active/finished/abandoned workflow |
| `quiz.TopScoreResponse` | N-1 run/question/choice; verified response and time |
| `multiplayer.MatchInvitation` | N-1 sender/recipient; pending/accepted/declined/cancelled workflow |
| `multiplayer.KnowledgeMatch` | 1-1 invitation; 1-N participants/rounds; waiting/active/completed/cancelled workflow |
| `multiplayer.MatchParticipant` | N-1 match/player; seat, hearts, ready/rematch/closed state |
| `multiplayer.MatchRound` | N-1 match/question; active/resolved workflow and winner |
| `multiplayer.MatchAnswer` | N-1 round/participant/choice; one answer per player and round |

The superuser can create, read, update, and delete registered records in Django Admin. The four-entity minimum is met by `User`, `Topic`, `Question`, and `AnswerChoice`, with real M-N and 1-N relations. The application implements additional entities for practice, workflow and multiplayer history.

## 4. Permission profiles

| Profile | Technical flags | Rights |
| --- | --- | --- |
| Player | authenticated, `is_staff=False` | Own profile, practice/offline sync, player search, invitations and owned matches |
| Staff operator | `is_staff=True`, `is_superuser=False` | Player rights plus custom admin console, aggregates, audit filtering, question creation, protected deactivation |
| Superuser | `is_staff=True`, `is_superuser=True` | All Django model permissions and complete Admin CRUD |

Authorization is checked in Django. React navigation hiding is only a usability convenience.

## 5. Required functional coverage

### Authentication and accounts

- Registration with unique username/email and ISO country code
- Login by username or email, logout, session restoration and optional remembered session
- Password-reset token flow
- Profile photo validation and favorite-topic preferences
- Offline cached identity after a prior successful online login

### CRUD and administration

- Full model CRUD through Django Admin for the superuser
- Staff console with aggregated dashboard and audit filter
- Validated creation of active questions with four distinct choices and one correct answer
- Protected user deactivation with self/superuser safeguards

### Status workflows

- Invitation: pending to accepted, declined or cancelled
- Match: waiting to active to completed/cancelled
- Round: active to resolved
- Practice run: active to finished/abandoned

Every transition checks current state, actor authorization, and relevant object ownership. Multi-record changes use database transactions.

### Search and dashboard

- Indexed username search with bounded results and query-count regression test
- Dashboard indicators for active users/topics/questions and matches grouped by status
- Audit filtering by action

### Audit trail

Sensitive staff operations create append-only application audit events containing actor, action, target, optional details, and timestamp. Django Admin also provides framework-level administration history.

## 6. Explicit business rules

1. Email addresses are unique and countries use uppercase two-letter codes.
2. An active question must have exactly four choices and exactly one correct choice.
3. A selected choice must belong to the submitted question.
4. A quiz answer cannot be replayed to increase score or response count.
5. Terminal practice runs reject further responses.
6. A player cannot invite themselves or create a duplicate pending invitation.
7. Match state and participant ownership govern readiness, answer, rematch and close operations.
8. Each participant has at most one answer per round.
9. Only one active round may exist per match.
10. Django calculates correctness, hearts, winners and synchronized offline score; client claims are not trusted.

## 7. Technology choices

- **Ionic, React and Capacitor:** a single TypeScript UI can run in desktop/mobile browsers and package for Android.
- **Django:** mature sessions, CSRF, relational ORM, validation, migrations, transactions and a production-ready administration surface.
- **PostgreSQL:** relational integrity and indexes for account, quiz, search and multiplayer data.
- **Docker Compose:** repeatable database startup and health checks without machine-specific PostgreSQL installation.
- **Vitest, Django TestCase and Cypress:** cover isolated client behavior, API/database integration and real-browser journeys.
- **k6, Bandit, ESLint, pip-audit, npm audit and ZAP:** provide executable performance, static, dependency and runtime security evidence.

## 8. Test strategy and measured results

| Layer | Result |
| --- | --- |
| Client unit/component/API | 31 passed |
| Backend model/API/integration | 66 passed |
| Browser E2E | 5/5 Chrome and 5/5 Firefox |
| Backend coverage | 80% |
| Performance | 20 VUs, 582 searches, 4.75 ms p95, 0% failures |
| Static analysis | ESLint passed; Bandit 0 medium/high findings |
| Dependency analysis | Python clean; npm 3 moderate and 0 high/critical |
| DAST | ZAP active scan 0 FAIL, 7 WARN, 136 PASS |
| Portability/build | Django/migration checks and production client build passed |

Machine-readable and human-readable evidence is under `reports/`. `npm run evidence:full` reproduces the core set.

## 9. Delivery inventory

| Brief deliverable | Repository artifact |
| --- | --- |
| Versioned source code | Git repository and commit history |
| Design report | This document and `docs/PROJECT_DESIGN.md` |
| Traceability matrix | `docs/TRACEABILITY_MATRIX.md` |
| Executable tests and reports | Test code plus `reports/` |
| ISO 25010 compliance report | `docs/ISO25010_COMPLIANCE_REPORT.md` |
| Installation/execution guide | `docs/INSTALLATION_AND_EXECUTION_GUIDE.md` |
| Live defense guide | `docs/LIVE_DEMONSTRATION_GUIDE.md` |

## 10. Known limitations

- Story and ranked matchmaking are clearly labelled placeholders outside the minimum brief.
- Friendly multiplayer uses one-second HTTP polling instead of WebSockets.
- npm reports three moderate router advisories whose proposed automatic fixes require breaking major-version upgrades.
- ZAP observations must be reassessed against a TLS-enabled production server with production response headers.
- The production client build succeeds but reports a large JavaScript chunk warning.

These limitations are disclosed so that every reported result remains traceable and honest, as required by the brief.
