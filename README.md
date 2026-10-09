# Mind Clash

A real-time two-player trivia game for Android. Two players race to answer the same question — the first correct answer (or closest numerical answer) wins the round, and the round loser loses one heart. The match ends when one player reaches zero hearts.

> **Status:** Initial project specification (v1.0)
> **Platforms:** Android application; web-based administration
> **Stack:** Ionic + React frontend; Django backend

---

## Table of Contents

- [Overview](#overview)
- [Game Rules at a Glance](#game-rules-at-a-glance)
- [Tech Stack](#tech-stack)
- [Monorepo Tooling](#monorepo-tooling)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Clone the Repository](#clone-the-repository)
  - [Frontend Setup (Ionic + React)](#frontend-setup-ionic--react)
  - [Backend Setup (Django)](#backend-setup-django)
- [Running the Project](#running-the-project)
- [Environment Configuration](#environment-configuration)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Architecture Notes](#architecture-notes)
- [Roadmap](#roadmap)
- [Definition of Done (MVP)](#definition-of-done-mvp)
- [License](#license)

---

## Overview

Mind Clash is a fast, competitive knowledge game in which two players race to answer the same question. Players can compete against another person through online matchmaking or play immediately against a clearly identified bot.

**MVP Product Promise:** Start a fair match in seconds, understand the result of every round, and complete a satisfying head-to-head session in approximately three to seven minutes.

### Success Measures

| Indicator | Initial Target |
|---|---|
| Match start reliability | ≥ 99% |
| Match completion rate | ≥ 90% |
| Service availability | ≥ 99.5% monthly |
| Round-result latency | p95 ≤ 750 ms |
| Crash-free sessions | ≥ 99.5% |
| Question quality | Monitored and improving |

---

## Game Rules at a Glance

### Default Match Configuration

| Rule | Default |
|---|---|
| Starting health | 3 hearts each |
| Question time | 10 seconds (bounded 5–30s) |
| Pre-round countdown | 3 seconds |
| Answer attempts | 1 (final submission) |
| Result display | At least 3 seconds |
| Reconnect grace period | 15 seconds |
| Maximum match duration | 10 minutes |

### Round Resolution

| Situation | Outcome |
|---|---|
| One correct; one wrong/unanswered | Correct player wins; opponent loses one heart |
| Both correct | Earlier valid submission wins; opponent loses one heart |
| Both wrong (non-numerical) | Draw; no heart lost |
| Neither submits | Draw; inactivity rules may apply |
| Exactly equal timestamps | Draw; no heart lost |
| Invalid or late answer | Treated as unanswered and logged |

### Numerical Questions

For an answer `x` and correct value `c`, the default error is `E = |x - c|`. Smaller error wins. Questions may optionally use relative error. Ties in error are resolved by earlier submission time; equal errors and equal timestamps produce a draw.

### Text Answers

Normalization may trim whitespace, case-fold, normalize Unicode, and match an approved alias list. Fuzzy matching is disabled by default.

### Disconnect, Quit & Inactivity

- Disconnected players get a 15-second grace period; the active round timer continues.
- Failing to reconnect before the grace period expires results in a forfeit.
- Explicitly quitting after round one starts is a forfeit.
- Three consecutive unanswered rounds may cause an inactivity forfeit after a warning.

---

## Tech Stack

| Layer | Component |
|---|---|
| Mobile | Ionic + React + Capacitor (Android UI) |
| HTTP API | Django + Django REST Framework |
| Real-time | Django Channels / ASGI |
| Persistence | PostgreSQL |
| Ephemeral State | Redis (channel layer, queue, presence, locks) |
| Jobs | Celery |
| Administration | Django Admin or custom staff UI |
| Deployment | Containerized services |

**Authority Boundaries:**
- The client renders state and sends intent; it never determines winners, official timing, or heart totals.
- The match consumer serializes commands per match and owns live state transitions.
- PostgreSQL is the source of truth for completed rounds and matches.
- Redis accelerates live play but must not be the only record of a completed outcome.

---

## Monorepo Tooling

The Ionic client and Django server are managed as one npm workspace with
[Turborepo](https://turborepo.com/). Run shared commands from the repository
root; Turbo dispatches each command to the workspaces that implement it and
caches non-development tasks.

| Root command | Purpose |
|---|---|
| `npm run dev` | Start the Ionic/Vite client and Django development server together |
| `npm run build` | Build the client and run Django's system check |
| `npm run check` | Run Django's system check |
| `npm run lint` | Lint every workspace that provides a `lint` script |
| `npm test` | Run client and server tests |
| `npm run test:e2e` | Build the client, then run its Cypress suite |

The root `package-lock.json` is the only npm lockfile. Add JavaScript packages
to a workspace from the root, for example:

```bash
npm install axios --workspace @mind-clash/client
npm install -D some-tool --workspace @mind-clash/server
```

Turbo configuration lives in `turbo.json`. The small `server/package.json`
does not replace Python packaging; it only exposes Django commands to Turbo.
Those commands automatically use `.venv` when it exists.

---

## Project Structure

```
mind-clash/
├── .gitignore
├── README.md
├── client/                      # Ionic + React frontend
│   ├── android/                 # Capacitor Android project
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/            # API + WebSocket clients
│   │   ├── hooks/
│   │   ├── theme/
│   │   └── App.tsx
│   ├── capacitor.config.ts
│   ├── ionic.config.json
│   └── package.json
├── server/                      # Django backend
│   ├── manage.py
│   ├── server/                  # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py              # Channels ASGI entrypoint
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/            # Users, profiles, auth
│   │   ├── matchmaking/         # Queue, tickets, lobby
│   │   ├── matches/             # Match engine, rounds, hearts
│   │   ├── questions/           # Questions, revisions, moderation
│   │   ├── bots/                # Bot profiles and behavior
│   │   └── reports/             # Question reports
│   ├── requirements.txt
│   └── .env.example
└── venv/                        # Python virtual environment (gitignored)
```

---

## Getting Started

### Prerequisites

Ensure the following are installed:

- **Node.js** (LTS) & **npm** — [nodejs.org](https://nodejs.org)
- **Ionic CLI** — `npm install -g @ionic/cli`
- **Python** 3.10+
- **PostgreSQL** 14+
- **Redis** 6+
- **Git**
- **Android Studio** (for building/running the Android app)

### Clone the Repository

```bash
git clone <your-repo-url> mind-clash
cd mind-clash
```

Install the root workspace dependencies (including Turborepo and the Ionic
client dependencies):

```bash
npm install
```

### Frontend Setup (Ionic + React)

```bash
npm run build --workspace @mind-clash/client
```

The Android project already exists under `client/android`; run
`npm exec --workspace @mind-clash/client -- cap sync android` after web builds
when native dependencies or configuration change.

### Backend Setup (Django)

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\Activate.ps1     # Windows PowerShell

# Install dependencies when server/requirements.txt is present
pip install -r server/requirements.txt

# Apply migrations
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser
```

---

## Running the Project

### Start the Django API

```bash
source .venv/bin/activate
npm run dev --workspace @mind-clash/server
```

API available at `http://localhost:8000/`.

### Start the Ionic App

```bash
npm run dev --workspace @mind-clash/client
```

Web preview available at `http://localhost:5173/`.

To start both development servers in one terminal, activate the Python virtual
environment and run:

```bash
npm run dev
```

### Run on Android Device/Emulator

```bash
npm run build --workspace @mind-clash/client
npm exec --workspace @mind-clash/client -- cap sync android
npm exec --workspace @mind-clash/client -- cap open android
```

Then run from Android Studio.

### Start Celery Worker (for background jobs)

```bash
cd server
source ../venv/bin/activate
celery -A server worker -l info
```

---

## Environment Configuration

All secrets enter through environment injection or a secret manager and are never committed.

Create a `.env` file in `server/` based on `server/.env.example`:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgres://user:password@localhost:5432/mindclash
REDIS_URL=redis://localhost:6379/0

ACCESS_TOKEN_LIFETIME_MINUTES=15
REFRESH_TOKEN_LIFETIME_DAYS=30

MATCH_QUESTION_TIMER_SECONDS=10
MATCH_RECONNECT_GRACE_SECONDS=15
MATCH_MAX_DURATION_SECONDS=600
```

For the client, create `client/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws/v1
```

---

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/match-engine
   ```
2. Make your changes, following the requirement IDs (e.g., `GME-01`, `MAT-04`) from the spec in commit messages and PR descriptions.
3. Run linting and tests locally before pushing.
4. Open a pull request. All `Must` requirements need linked passing tests or an approved waiver.

### Recommended VS Code Extensions

- **ESLint** — JavaScript/TypeScript linting
- **Prettier** — Code formatting
- **Python** — Microsoft Python extension
- **Pylance** — Python language server
- **Django** — Django template & syntax support
- **GitLens** — Git supercharged

---

## Testing

### Frontend (Ionic + React)

```bash
npm test                                      # all workspace tests
npm run test --workspace @mind-clash/client   # client unit/component tests
npm run test:e2e                              # client end-to-end tests
```

### Backend (Django)

```bash
source .venv/bin/activate
npm run test --workspace @mind-clash/server
```

### Test Strategy Overview

| Level | Coverage |
|---|---|
| Unit | Normalization, numerical comparison, ties, state transitions, bot sampling |
| Property-based | Symmetry, max one heart lost, health bounds, terminal invariants |
| API integration | Authentication, permissions, idempotency, migrations, errors |
| WebSocket integration | Ordering, duplicate commands, reconnect, deadline boundaries |
| Mobile component | Answer controls, locked state, errors, accessibility, timers |
| End-to-end | Guest PvP, account PvP, bot, reconnect, forfeit, report, history |
| Load & soak | Concurrent rooms, queue throughput, Redis/DB behavior, leaks |
| Security | Authorization, token handling, limits, dependencies, configuration |

### MVP Acceptance Scenarios

1. Two clients enter matchmaking, receive identical rounds, and display identical authoritative heart totals.
2. When both players answer correctly, the earlier server-received answer wins and exactly one heart is removed.
3. For numerical answers, the smaller configured error wins regardless of speed.
4. Equal numerical errors are resolved by submission time; a true timestamp tie loses no heart.
5. A late answer is rejected and cannot alter a resolved round.
6. A duplicate answer command creates no duplicate record and returns its original acknowledgement.
7. A reconnecting client receives an accurate snapshot without replaying old heart changes as new.
8. Reaching zero hearts creates one terminal result, stored once and visible in both histories.
9. A bot's committed answer remains independent of the human answer and follows its profile.
10. A retired question cannot enter a new match but remains available in historical review.

---

## Architecture Notes

### Real-Time Contract

WebSocket route: `/ws/v1/matches/{match_id}`. Authentication uses an initial auth message or secure subprotocol — **never** a long-lived token in the URL.

Key events include `client.ready`, `answer.submit`, `state.request`, `heartbeat` (client → server), and `match.snapshot`, `round.started`, `answer.accepted` (server → client).

### Consistency & Reconnection

- Each active match has one logical command owner.
- Every client command includes an idempotency key.
- Every server event has a monotonically increasing sequence number.
- A client detecting a gap requests a state snapshot.
- Answer receipt and round resolution are persisted transactionally or via a reliable outbox pattern.

### Security & Fair Play

- TLS for all traffic; secure headers; strict allowed hosts and origins.
- Short-lived access tokens, rotating refresh tokens, revocation.
- Object-level authorization on every match/history/report operation.
- Rate limits on auth, queue changes, answers, reports, reconnects.
- Answer keys are never included in active-round payloads.
- Server receipt time is authoritative; no manipulable latency compensation.

### Privacy

Collect only account, gameplay, session, diagnostic, and moderation data required to operate the service. No precise location — region must remain coarse. Account deletion and data export are supported.

---

## Roadmap

### Post-MVP

- Ranked seasons and leaderboards
- Friend challenges
- Achievements and cosmetic rewards
- Daily challenges
- Tournaments
- Richer statistics
- Additional languages
- Adaptive question difficulty
- iOS distribution

Each feature is assessed against fairness, moderation, retention, and operational cost.

---

## Definition of Done (MVP)

Mind Clash MVP is complete when two Android users — or one user and a clearly labeled bot — can reliably finish a server-authoritative three-heart match, understand every round outcome, reconnect safely, review the result, and report flawed content, with production monitoring and tested recovery in place.

---

## License

TBD — to be finalized before public release.
