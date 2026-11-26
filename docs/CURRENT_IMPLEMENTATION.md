# Clash of Minds: Current Implementation Guide

Last updated: November 26, 2026

This document explains what is implemented in Clash of Minds today. It is written for developers who are new to Ionic, React, or Django and need a practical map of the project before changing it.

The root `README.md` contains the broader product vision. Some items in that original specification, such as WebSockets, Redis, Celery, ranked matchmaking, and bots, are future work. This guide describes the code that actually exists now.

## 1. What the application can do

The current application supports:

- Account registration, login, logout, and session restoration.
- A top-score practice mode using all quiz categories.
- A category practice mode using questions from one selected category.
- Adaptive online practice based on saved accuracy, response time, topic, and question history. A PyTorch model can replace the cold-start history estimator once enough real responses are available.
- Offline practice after the player has logged in online at least once.
- Local storage of completed offline games.
- Automatic synchronization of offline games when connectivity returns.
- Friendly multiplayer invitations between registered players.
- A two-player knowledge duel with synchronized questions, hearts, timers, forfeits, rematches, and room cleanup.
- An Ionic web build and an existing Capacitor Android project.

Ranked matchmaking, story mode, bots, WebSockets, and production deployment are not implemented yet.

The adaptive neural model is experimental and is not active until trained on enough real player responses. The application remains usable with the history-based selector while that data is collected. See [Adaptive Question Selection](ADAPTIVE_QUESTION_SELECTION.md) for training and evaluation steps.

## 2. The architecture in plain language

There are three main pieces:

```text
Ionic + React client
        |
        | HTTP requests returning JSON
        v
Django application
        |
        | Django ORM queries
        v
PostgreSQL database
```

### Ionic

Ionic supplies mobile-friendly visual components such as buttons, modals, alerts, and page containers. It also allows the web application to be packaged as an Android application through Capacitor.

### React

React controls the client-side screens and state. A React component is a TypeScript function that returns UI markup. Hooks such as `useState`, `useEffect`, and `useCallback` store state and run logic when that state changes.

### Django

Django is the backend. It authenticates users, validates requests, applies game rules, and writes permanent data to PostgreSQL. Django models describe database tables, views implement API behavior, and URL files connect HTTP paths to views.

### PostgreSQL

PostgreSQL stores accounts, questions, answers, scores, invitations, rooms, rounds, and multiplayer answers. Docker Compose provides the local database on port `5433`.

### How the client and server communicate

The client calls relative URLs such as `/api/auth/me/`. During development, Vite proxies `/api` requests to Django at `http://127.0.0.1:8000`.

Authentication uses Django's session cookie. Mutating requests also send Django's CSRF token. The browser includes both because requests use `credentials: 'same-origin'`.

Multiplayer currently uses HTTP polling. While a room is open, each client requests its latest state once per second. There is no WebSocket connection yet.

## 3. Repository map

```text
Clash-of-minds/
|-- accounts/                    Django user model and authentication API
|-- quiz/                        Questions, practice games, offline sync
|-- multiplayer/                 Invitations, rooms, rounds, duel rules
|-- server/                      Django settings and root URL configuration
|-- client/
|   |-- src/components/          Reusable React UI components
|   |-- src/features/auth/       Auth API, context, cached user
|   |-- src/features/quiz/       Online and offline quiz logic
|   |-- src/features/sync/       Offline synchronization manager
|   |-- src/features/multiplayer Multiplayer API client and types
|   |-- src/pages/               Application screens
|   |-- src/routing/             React routes and auth protection
|   `-- android/                 Capacitor Android project
|-- scripts/                     Helpers for local development
|-- compose.yaml                 Local PostgreSQL container
|-- manage.py                    Django command entry point
|-- package.json                 npm workspaces and root commands
`-- turbo.json                   Monorepo task configuration
```

Important starting points:

- `client/src/routing/GameRouter.tsx`: maps URLs to React pages.
- `client/src/features/auth/AuthContext.tsx`: restores and exposes authentication state.
- `client/src/pages/practice/top-score/PracticeTopScore.tsx`: practice gameplay screen.
- `client/src/pages/multiplayer/friendly/FriendlyMatch.tsx`: invitations and rooms.
- `client/src/pages/multiplayer/match/MatchRoom.tsx`: multiplayer duel screen.
- `server/urls.py`: root Django API routes.
- `accounts/views.py`: authentication endpoints.
- `quiz/views.py`: online practice and offline synchronization rules.
- `multiplayer/views.py`: invitation, room, timer, answer, rematch, and close rules.

## 4. Local setup on Windows

### Prerequisites

Install:

- Git
- Node.js and npm
- Python
- Docker Desktop
- Android Studio only if Android testing is needed

### Install JavaScript dependencies

From the repository root:

```powershell
npm install
```

The project uses npm workspaces. There is one root `package-lock.json`; do not create a second lockfile inside `client` or `server`.

### Create the Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r server\requirements.txt
```

Use the explicit project interpreter when there is any doubt:

```powershell
.\.venv\Scripts\python.exe manage.py <command>
```

Running only `python.exe manage.py ...` may select an unrelated Python installation from `PATH`.

### Create the Django environment file

```powershell
Copy-Item server\.env.example server\.env
```

The development defaults expect PostgreSQL at `localhost:5433`.

### Start PostgreSQL

Make sure Docker Desktop is running, then execute:

```powershell
npm run db:up
```

### Apply migrations and seed questions

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_quiz
```

`seed_quiz` creates or updates 6 topics and 30 questions. It updates existing answer choices in place so saved game responses keep valid foreign keys. It is safe to run more than once.

### Start the application

Run both Django and Vite:

```powershell
npm run dev
```

Then open:

- Client: `http://localhost:5173`
- Django: `http://localhost:8000`
- Django admin: `http://localhost:8000/admin/`

To expose both servers to devices on the same classroom or home network:

```powershell
npm run dev:network
```

The command prints the LAN URLs. Windows Firewall may ask for permission. Both devices must be able to reach the development computer.

## 5. Authentication and persisted login

### Online session

Django creates a server-side session when login succeeds. The browser stores the session cookie and sends it with later API requests. On application startup, the client calls:

```text
GET /api/auth/me/
```

If the session is valid, the player is immediately restored without entering credentials again.

### Cached offline identity

After a successful online login, the client also stores a small user object in `localStorage` under:

```text
clash-of-minds:authenticated-user
```

If `/api/auth/me/` fails because the device is offline, React uses this cached identity. This does not create a new Django session; it lets the known player access already-downloaded offline content.

Important consequence: a player must sign in online at least once before offline play is possible.

The main files are:

- `client/src/features/auth/AuthContext.tsx`
- `client/src/features/auth/storage.ts`
- `client/src/features/auth/api.ts`
- `accounts/views.py`

## 6. Practice and offline mode

### Online practice

Top-score practice has a 10-second timer per question. A correct answer increases the score and loads another question. A wrong answer or timeout ends the run.

Category practice uses the same game engine but sends a `topicSlug`, so Django only selects questions from that topic.

The server is authoritative online: it verifies the selected choice and calculates the official score.

### Downloading the offline catalog

While authenticated and connected, the synchronization manager requests:

```text
GET /api/quiz/offline/catalog/
```

The response contains active questions, answer choices, correct choice IDs, the timer, and the player's best score. It is cached separately for each user.

### Playing offline

Offline runs are handled in `client/src/features/quiz/offline.ts`. The client:

1. Loads the cached question catalog.
2. Creates a UUID for the local run.
3. Records each selected answer and response time.
4. Updates the local score.
5. Moves completed runs into a pending synchronization queue.

Relevant local storage keys are scoped by user ID:

```text
clash-of-minds:offline-catalog:<userId>
clash-of-minds:offline-runs:<userId>
```

### Synchronizing after reconnection

`SyncManager` runs after authentication and listens for the browser's `online` event. If pending runs exist, it opens the Synchronization modal and posts up to 100 runs at a time to:

```text
POST /api/quiz/offline/sync/
```

Django does not trust the score sent by the phone. It replays the submitted answers using database questions, recalculates the score, and saves the verified result. Run UUIDs make synchronization idempotent: retrying the same run does not create a duplicate.

After successful synchronization, the client removes those runs from its pending queue and refreshes the offline catalog.

## 7. Friendly multiplayer flow

### Invitation lifecycle

1. Player A searches for Player B.
2. Player A sends an invitation.
3. Player B accepts or declines it.
4. Acceptance creates one `KnowledgeMatch` and two `MatchParticipant` rows.
5. Both players open the room and press **I'm ready**.
6. When both are ready, Django starts the duel and creates the first round.

Django prevents self-invitations and duplicate pending invitations between the same two players.

### Duel rules currently implemented

| Rule | Current behavior |
|---|---|
| Starting health | 3 hearts per player |
| Whole duel timer | 5 minutes |
| Question timer | 15 seconds |
| Question | Same question for both players |
| Choices | Same four choices, shown in a different order |
| Answer attempts | One per player per round |
| First response | Locked; the round waits for the opponent or deadline |
| One correct answer | Correct player wins; opponent loses one heart |
| Both correct | Earlier server-recorded answer wins |
| Both wrong | Draw; no heart is lost |
| No correct answer at deadline | Draw; a new round begins |
| One correct answer at deadline | Correct player wins even if the opponent did not answer |
| Zero hearts | Duel ends immediately |
| Five-minute deadline | Player with more hearts wins; equal hearts produce a draw |

The server, not the React screen, resolves rounds and changes hearts.

### Why both clients stay synchronized

The room page fetches current match state every second. Django returns:

- Match status and remaining match time.
- Both participants and their hearts.
- Current question and question time remaining.
- Whether the current player has answered.
- The previous round result.
- Final winner and end reason.

The visible countdowns update locally between polls, but Django timestamps decide whether an answer is late.

### Closing and forfeiting

The back/close action first displays an **Are you sure?** confirmation.

- Closing an active duel is a forfeit.
- Django immediately completes the duel and makes the other player the winner.
- The remaining player sees `Winner!` with `Opponent left the room` on the next poll.
- Each participant has a `closed_at` timestamp.
- The database room is deleted after both participants have closed it.
- If a client polls a room that has already been deleted, React automatically returns that player to the friendly lobby instead of showing a stale error screen.

### Rematches

After a completed duel, each player can press **Rematch**.

- One request displays `Waiting for opponent...`.
- When both request a rematch, Django creates a fresh invitation and room.
- Both clients discover the new room through polling and automatically navigate to it.
- The new room begins in the waiting state, so both players must ready up again.

## 8. Django multiplayer data model

### `MatchInvitation`

Stores sender, recipient, status, and response time. Status is pending, accepted, declined, or cancelled.

### `KnowledgeMatch`

Represents the room and overall duel. It stores status, winner, start/end timestamps, end reason, and the optional room created for a rematch.

Match status is waiting, active, completed, or cancelled. Current end reasons are hearts, time, and forfeit.

### `MatchParticipant`

Connects a user to a room. It stores host/guest seat, score, hearts, readiness, rematch consent, and room-close time.

### `MatchRound`

Connects one question to one match sequence. It stores active/resolved state, the round winner, and timestamps. A database constraint permits only one active round per match.

### `MatchAnswer`

Stores one participant's choice for one round. A database constraint permits only one answer per participant per round. The model verifies that the choice belongs to the round's question.

## 9. Current API reference

All endpoints require an authenticated Django session unless noted by the login/register flow.

### Authentication

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register/` | Create an account |
| POST | `/api/auth/login/` | Start a session |
| POST | `/api/auth/logout/` | End the session |
| GET | `/api/auth/me/` | Restore the current user |

### Practice and offline synchronization

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/quiz/top-score/start/` | Start all-topic or category practice |
| POST | `/api/quiz/top-score/<runId>/answer/` | Submit an online answer |
| POST | `/api/quiz/top-score/<runId>/quit/` | Quit an online run |
| GET | `/api/quiz/offline/catalog/` | Download the offline question pack |
| POST | `/api/quiz/offline/sync/` | Import and verify offline runs |

### Friendly multiplayer

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/multiplayer/players/?q=<name>` | Search players |
| GET | `/api/multiplayer/invitations/` | List invitations |
| POST | `/api/multiplayer/invitations/send/` | Send an invitation |
| POST | `/api/multiplayer/invitations/<id>/respond/` | Accept or decline |
| POST | `/api/multiplayer/invitations/<id>/cancel/` | Cancel a pending invitation |
| GET | `/api/multiplayer/matches/` | List the player's open rooms |
| GET | `/api/multiplayer/matches/<id>/` | Fetch current room state |
| POST | `/api/multiplayer/matches/<id>/ready/` | Mark the player ready |
| POST | `/api/multiplayer/matches/<id>/answer/` | Submit a round answer |
| POST | `/api/multiplayer/matches/<id>/rematch/` | Request a rematch |
| POST | `/api/multiplayer/matches/<id>/close/` | Close/forfeit the room |

## 10. Testing the project

### Run everything

```powershell
npm test
npm run lint
npm run build
```

### Django only

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

### Client only

```powershell
npm test --workspace @mind-clash/client
npm run lint --workspace @mind-clash/client
npm run build --workspace @mind-clash/client
```

The client uses Vitest, Testing Library, and jsdom. Django uses its built-in `TestCase` runner and creates a temporary PostgreSQL test database.

The main regression coverage includes:

- Authentication and protected routes.
- Online and offline practice.
- Idempotent offline synchronization.
- Idempotent quiz seeding even when saved responses reference choices.
- Invitation authorization and duplicate protection.
- Starting only after both players are ready.
- Same-question/different-order multiplayer payloads.
- Waiting for both answers or the question deadline.
- Heart loss, match timer, draws, forfeits, rematches, and room deletion.
- Redirecting away from a deleted multiplayer room.

## 11. Testing multiplayer with two players

### On one computer

1. Start PostgreSQL and the development servers.
2. Open `http://localhost:5173` in a normal browser window.
3. Open the same URL in a private/incognito window or a different browser.
4. Register two separate users.
5. From Player A, open Friendly Match and invite Player B.
6. From Player B, accept the invitation.
7. Open the created room on both clients.
8. Press **I'm ready** on both.

Separate browser profiles are necessary because one browser profile shares one Django session cookie.

### With phones in class

1. Connect the computer and both phones to the same Wi-Fi network.
2. Run `npm run dev:network`.
3. Use the printed client network URL on both phones.
4. Allow Node.js/Python through Windows Firewall if prompted.
5. Follow the same two-account invitation flow.

Some school networks block communication between devices. If the phones cannot reach the printed address, use a personal hotspot or a network that allows peer devices.

## 12. Safe patterns for new development

### Adding a Django field

1. Edit the model.
2. Generate a migration:

   ```powershell
   .\.venv\Scripts\python.exe manage.py makemigrations
   ```

3. Inspect the generated migration.
4. Apply it:

   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ```

5. Add or update tests.

Never edit a production database table manually when a migration can describe the change.

### Adding an API endpoint

1. Add the server logic to the Django app's `views.py`.
2. Register it in that app's `urls.py`.
3. Check authentication and object ownership.
4. Use a transaction for multi-row game state changes.
5. Add an API function and TypeScript types on the client.
6. Update the React screen.
7. Test successful, unauthorized, duplicate, and late requests.

### Keeping game logic authoritative

The client may animate countdowns and display predicted state, but Django must decide:

- Whether an answer arrived before the deadline.
- Whether an answer is correct.
- Who won a round or match.
- How many hearts each player has.
- Whether an offline score is valid.

This prevents two clients from disagreeing and makes cheating harder.

## 13. Known limitations and sensible next steps

### Current limitations

- Multiplayer polls every second instead of using WebSockets.
- There is no reconnect grace period or online-presence tracking.
- Ranked matchmaking is still a placeholder.
- Story mode is still a placeholder.
- Offline data uses browser `localStorage`; a native SQLite/Capacitor storage layer would be more durable for production mobile use.
- The complete offline catalog contains correct answer IDs because offline scoring must work without a server. Production anti-cheat expectations should account for this.
- There is no deployment configuration or CI pipeline yet.
- The production client build reports Ionic CSS compatibility and large-bundle warnings. The build succeeds, but code splitting is a future optimization.

### Recommended next steps

1. Add WebSocket or Server-Sent Event updates for faster multiplayer state delivery.
2. Add presence and reconnect grace handling.
3. Move tunable timer values into Django settings/environment variables.
4. Add match history and player statistics screens.
5. Replace or supplement `localStorage` with durable native storage.
6. Add end-to-end tests using two authenticated browser contexts.
7. Add CI that runs Django tests, Vitest, ESLint, migration checks, and the production build.

## 14. Troubleshooting

### `python.exe manage.py ...` fails before Django starts

Use the project's interpreter explicitly:

```powershell
.\.venv\Scripts\python.exe manage.py <command>
```

### PostgreSQL connection fails

Check Docker Desktop, then run:

```powershell
npm run db:up
npm run db:logs
```

Confirm that `server/.env` exists and uses port `5433`.

### No questions are available

Run:

```powershell
.\.venv\Scripts\python.exe manage.py seed_quiz
```

### Offline mode says questions are not downloaded

Connect to the internet, log in, and let the application successfully load once. This restores the Django session and downloads the offline catalog.

### Two test players keep becoming the same user

Use separate browser profiles, different browsers, or one normal and one private window. Tabs in the same profile share cookies.

### A terminated room remains on screen

The room page polls once per second. When Django returns `404` for a deleted room, the client routes back to the friendly lobby automatically.

## 15. Current Git baseline

The implementation described here was merged into `main` through merge commit:

```text
d9997e9 merge: complete friendly multiplayer duels
```

When this document changes alongside future features, update the date, implemented-feature list, rules, tests, limitations, and Git baseline so the guide stays trustworthy.
