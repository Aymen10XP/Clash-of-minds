# Mind Clash: Project Design

## Purpose and scope

Mind Clash is a browser/mobile trivia game with solo practice, offline play, and two-player multiplayer. Players answer questions; the Django API validates submissions and owns persisted scores and match state. Ionic/React presents the game and communicates with the API. Django Admin and a staff-only Ionic console support content and account administration.

## Architecture

```text
Ionic + React + Capacitor
  ├─ session, quiz, offline queue, multiplayer, staff console
  └─ HTTP requests /api/auth, /api/quiz, /api/multiplayer
                 │
                 ▼
Django application
  ├─ accounts: users, sessions, preferences, audit events
  ├─ quiz: topics, questions, choices, top-score runs/responses
  ├─ multiplayer: invitations, matches, participants, rounds, answers
  └─ Django Admin: staff-managed records and admin action history
                 │
                 ▼
PostgreSQL for local application data; SQLite in the automated Django test settings
```

This diagram describes the implementation in this repository. The README contains an earlier target architecture in places; Redis, Celery, and a separate Channels service are not requirements for the current demo setup.

## Data model

| Entity | Relationships and purpose |
| --- | --- |
| `accounts.User` | Account identity, staff/superuser permissions, country and favorite-topic relation |
| `quiz.Topic` | Groups questions and can be selected as a user preference |
| `quiz.Question` | Belongs to a topic; has a difficulty and active/inactive publishing state |
| `quiz.AnswerChoice` | Belongs to one question; exactly one correct choice is required for an active question |
| `quiz.TopScoreRun` | Belongs to a user and tracks a practice run through active, finished, or abandoned states |
| `quiz.TopScoreResponse` | Belongs to a run and question; stores one graded answer event |
| `multiplayer.MatchInvitation` | Connects sender and recipient and moves through pending/accepted/declined/cancelled states |
| `multiplayer.KnowledgeMatch` | Owns a match lifecycle and its participants and rounds |
| `multiplayer.MatchParticipant` | Connects a user to a match and stores readiness/remaining hearts |
| `multiplayer.MatchRound` | Belongs to a match and question; tracks active/resolved state |
| `multiplayer.MatchAnswer` | Belongs to a round and participant and stores the server-graded response |
| `accounts.AuditEvent` | Append-only application record for selected staff actions, with nullable actor and target metadata |

Django Admin exposes model management for staff, including question/choice inline editing and model search/filter fields. The custom staff console adds question creation, user deactivation, aggregate indicators, and a filterable recent audit-event list.

## Roles and access boundaries

- **Player:** normal authenticated account. Can play, update permitted profile preferences, and view only authorized match data.
- **Staff operator:** `is_staff=True`; can use the custom staff console and any explicitly granted Django Admin permissions.
- **Superuser:** `is_superuser=True`; Django grants all model permissions and complete registered-model CRUD.

`npm run seed:demo` creates one local demonstration account for each profile: `demo_player`, `demo_admin`, and `demo_superuser`.

The role boundaries are enforced on the server. Hiding the admin navigation item in React is only a usability measure, not the authorization check.

## Technology choices

- **Ionic + React + Capacitor:** one TypeScript UI supports desktop/mobile browser testing and Android packaging.
- **Django:** combines a relational ORM, sessions, server-side validation, migrations, and a useful staff administration site.
- **PostgreSQL:** the configured local application database supports relational integrity for account, quiz, and match relationships.
- **SQLite test settings:** fast, self-contained tests that do not need a running PostgreSQL service; this is not proof of identical behavior under PostgreSQL.
- **Vitest/Testing Library and Django TestCase:** component/API-facing client checks plus backend model/API integration tests.
- **Cypress:** browser-level route, accessibility, login-error, and mobile-width checks. The official Cypress 16.3.0 Docker image passes all five journeys in both Chrome 157 and Firefox 160.

## Important business rules

1. Account email is unique; profile country uses a two-letter uppercase country code.
2. A question must belong to a topic; activating it requires four choices and exactly one correct answer.
3. Answer choices are unique within the question creation API; the selected correct choice must belong to the current question.
4. An online quiz response cannot be replayed to increase score or response count.
5. A top-score run has one lifecycle; terminal runs cannot accept more responses.
6. Match operations are restricted to participants; match/round status transitions govern readiness, answers, and resolution.
7. A player receives at most one answer opportunity per round; server-side validation determines correctness and outcome.
8. Staff cannot deactivate their own account through the custom user-management API, and superusers are protected from that operation.

Automated checks for these rules are in `accounts/tests.py`, `quiz/tests.py`, and `multiplayer/tests.py`. The quality evidence document names representative test cases.

## Repository map

```text
accounts/                 Django account, profile, access and audit behavior
quiz/                     Django question catalog, practice and scoring behavior
multiplayer/              Django invitations, matches and round resolution
client/src/features/      Frontend API/session/offline feature modules
client/src/pages/         Ionic application screens
client/cypress/           Browser-level Cypress suite and its TypeScript project
tests/performance/        k6 player-search load scenario (requires a running server)
docs/                     design, quality evidence, and presentation instructions
```

## Local setup summary

For the full reproducible commands, see [README.md](../README.md) and the student-facing [live demonstration guide](LIVE_DEMONSTRATION_GUIDE.md). The demo backend currently expects PostgreSQL as configured by `server/.env`; the automated Django test suite uses in-memory SQLite.
