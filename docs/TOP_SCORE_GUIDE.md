# Top Score Mode: Django and Ionic Implementation Guide

This guide explains the complete Top Score feature, from the PostgreSQL tables to the playable Ionic screen. It is written for someone who is still getting comfortable with Django and React.

## 1. What the feature does

Top Score is a solo quiz run with these rules:

- The player must be logged in.
- Every question belongs to a category.
- A question has exactly four possible answers and exactly one correct answer.
- The player has 10 seconds to answer.
- A correct answer adds one point and starts another question after a short feedback pause.
- A wrong answer or timeout ends the run.
- The final score and the player's best score are stored in PostgreSQL.
- Questions do not repeat until the current question bank has been exhausted.
- The correct answer is never sent to the client before the player answers.

The implementation follows an important game-development rule: **the server is authoritative**. Ionic displays the game and sends the player's choice, but Django decides whether the answer is valid, whether it arrived on time, and what the new score is.

## 2. Main files

### Django

| File | Responsibility |
|---|---|
| `quiz/models.py` | Database structure and model validation |
| `quiz/views.py` | Start, answer, and quit API logic |
| `quiz/urls.py` | Quiz API URL definitions |
| `quiz/admin.py` | Django admin screens for quiz data and runs |
| `quiz/tests.py` | Model, seed-command, and API tests |
| `quiz/management/commands/seed_quiz.py` | Repeatable starter-data command |
| `quiz/migrations/0001_initial.py` | Initial quiz tables and constraints |
| `quiz/migrations/0002_*.py` | Active-question state and endless-run support |
| `server/settings.py` | Registers the `quiz` Django application |
| `server/urls.py` | Mounts quiz URLs below `/api/quiz/` |

### Ionic and React

| File | Responsibility |
|---|---|
| `client/src/features/quiz/api.ts` | Typed calls to the Django quiz API |
| `client/src/features/quiz/feedback.ts` | Correct/wrong sounds and haptic feedback |
| `client/src/pages/practice/top-score/PracticeTopScore.tsx` | Game state and rendered screen |
| `client/src/pages/practice/top-score/PracticeTopScore.css` | Responsive game layout and animations |

## 3. Django application setup

The feature lives in its own Django app named `quiz`. It is registered in `server/settings.py`:

```python
INSTALLED_APPS = [
    # Django applications...
    'accounts.apps.AccountsConfig',
    'quiz.apps.QuizConfig',
]
```

Registering an application tells Django to load its models, migrations, admin configuration, and other app-level behavior.

The project URL file includes the quiz URL file:

```python
path('api/quiz/', include('quiz.urls')),
```

The resulting endpoints are:

```text
POST /api/quiz/top-score/start/
POST /api/quiz/top-score/<run UUID>/answer/
POST /api/quiz/top-score/<run UUID>/quit/
```

All three endpoints require an authenticated Django session.

## 4. Database models

### 4.1 `Topic`

A topic is a question category such as `Computing & AI` or `Ancient Civilizations`.

Important fields:

- `slug`: stable URL/code-friendly identifier, such as `computing`.
- `title`: player-facing category name.
- `description`: short explanation.
- `is_active`: allows a topic to be enabled or disabled.
- `sort_order`: controls display order.

The `slug` and `title` are unique so duplicate categories cannot be created accidentally.

### 4.2 `Question`

Each question has:

- A required `topic` foreign key.
- The question `prompt`.
- An optional `explanation` for future result/review screens.
- A difficulty: `easy`, `medium`, or `hard`.
- An `is_active` flag.
- Creation and update timestamps.

`on_delete=models.PROTECT` is used for the topic relationship. Django will refuse to delete a topic if questions still depend on it. This protects quiz history from becoming incomplete.

Inactive questions behave like drafts. Before an administrator activates a question, model validation requires exactly four choices and exactly one correct choice:

```python
if choice_count != 4:
    errors.append('An active question must have exactly four choices.')
if correct_count != 1:
    errors.append('An active question must have exactly one correct choice.')
```

The model calls `full_clean()` from `save()`. This means the same rules apply whether data comes from Django admin, a command, or application code.

### 4.3 `AnswerChoice`

An answer choice contains:

- Its parent question.
- Its visible text.
- A position from 1 to 4.
- `is_correct`, which identifies the answer key.

Database constraints enforce important invariants:

- A question cannot have two choices in the same position.
- A question cannot have more than one correct choice.
- Positions must be between 1 and 4.

An active question must be deactivated before its choices can be structurally edited. This avoids serving a half-edited question to a player.

### 4.4 `TopScoreRun`

A run represents one play session for one authenticated user.

Important fields:

- `client_run_id`: a public UUID used by the API instead of exposing a sequential database ID.
- `user`: the account that owns the run.
- `status`: `active`, `finished`, or `abandoned`.
- `end_reason`: wrong answer, timeout, or quit.
- `score`: authoritative score maintained by Django.
- `current_question`: the only question the server will accept for this run.
- `question_started_at`: authoritative start time for the current question.
- `started_at` and `ended_at`: run timestamps.

Keeping `current_question` on the run prevents a modified client from submitting an answer to an easier or unrelated question.

The model also validates consistent states. For example, an active run cannot have an end time, while a completed run must have an end time and reason.

### 4.5 `TopScoreResponse`

A response records each answered question:

- The run and question.
- The selected choice, or `NULL` for a timeout.
- Its sequence number in the run.
- Response time in milliseconds.
- Whether it was correct.
- The submission timestamp.

The client never supplies `is_correct`. During `save()`, Django derives it from the selected database choice:

```python
self.is_correct = self.selected_choice.is_correct
```

This prevents a player from sending `{ "isCorrect": true }` and awarding themselves points.

Response time is constrained to the valid range of 0 through 10,000 milliseconds. Sequence numbers are unique inside a run.

The original design prevented a question from appearing twice in one run. That constraint was removed in migration `0002` so Top Score can continue after all available questions have been used. The API still avoids repeats until it has exhausted the active bank.

## 5. Starter question data

The custom management command creates:

- 6 categories.
- 30 active questions.
- 5 questions per category.
- 4 choices per question.
- 120 choices in total.

Run it from the repository root:

```powershell
.\.venv\Scripts\python.exe manage.py seed_quiz
```

The command uses `update_or_create()` for topics and `get_or_create()` for questions. It is idempotent: running it again updates the same starter content instead of duplicating it.

When updating a question, the command performs this safe order:

1. Deactivate the question.
2. Delete its old choices.
3. Recreate all four choices.
4. Reactivate the completed question.

The entire command uses `@transaction.atomic`. If any question fails, PostgreSQL rolls back the command instead of keeping partial data.

Correct answers are distributed across positions 1 through 4. The API additionally shuffles choices before returning them, so players cannot learn a position pattern.

## 6. API behavior

### 6.1 Starting a run

Request:

```http
POST /api/quiz/top-score/start/
```

Django:

1. Rejects anonymous users with HTTP 401.
2. Marks any older active run for that user as abandoned.
3. Creates a new `TopScoreRun`.
4. Selects a random active question.
5. Stores that question and its start time on the run.
6. Returns the run, score, best score, time limit, and safe question payload.

Example response:

```json
{
  "runId": "338ba197-9c2a-4cf2-a9c9-f20f05d8f511",
  "score": 0,
  "bestScore": 7,
  "timeLimitMs": 10000,
  "question": {
    "id": 12,
    "topic": {
      "slug": "revolutions",
      "title": "Age of Revolutions"
    },
    "prompt": "In which year was the United States Declaration of Independence adopted?",
    "difficulty": "easy",
    "choices": [
      { "id": 46, "text": "1783" },
      { "id": 45, "text": "1776" },
      { "id": 47, "text": "1789" },
      { "id": 44, "text": "1765" }
    ]
  }
}
```

Notice that choices do not contain `is_correct`.

### 6.2 Answering

Request:

```http
POST /api/quiz/top-score/<run UUID>/answer/
Content-Type: application/json

{
  "questionId": 12,
  "choiceId": 45
}
```

For a timeout, Ionic sends `choiceId: null`.

The view uses both `@transaction.atomic` and `select_for_update()`. The transaction makes the operation all-or-nothing, while the row lock prevents two almost-simultaneous taps or requests from both changing the same run.

Django validates that:

- The run belongs to the logged-in user.
- The run is still active.
- The submitted question is the run's current question.
- The selected choice belongs to that question.
- The response is inside the server's deadline.

The server measures elapsed time using `question_started_at`; it does not trust a time reported by the phone. A small network grace period prevents normal request travel time from unfairly rejecting a last-moment tap.

On a correct answer, Django:

1. Stores the response.
2. Adds one to the score.
3. Selects and stores the next question.
4. Returns the updated score and next question.

On a wrong answer or timeout, Django:

1. Stores the response.
2. Marks the run finished.
3. Stores its end reason and end time.
4. Returns the correct choice ID so Ionic can show the result animation.

### 6.3 Quitting

When the player presses Back during an active run, Ionic sends:

```http
POST /api/quiz/top-score/<run UUID>/quit/
```

Django changes the run to `abandoned` with the reason `quit`. Calling this endpoint after the run already ended is safe.

## 7. CSRF and authentication

The quiz uses the same Django session authentication as registration and login.

Before a POST request, `client/src/features/quiz/api.ts` ensures the browser has a CSRF cookie by requesting `/api/auth/me/`. It then sends:

```text
credentials: same-origin
X-CSRFToken: <csrftoken cookie value>
Content-Type: application/json
```

The session cookie identifies the user. The CSRF token proves that the POST came from the application rather than an unrelated malicious website.

During Vite development, `/api` requests use the proxy in `client/vite.config.ts`, so the browser sees the Ionic client and API as the same origin. This also works when opening the Vite network address from a phone.

## 8. Ionic game state

`PracticeTopScore.tsx` is a small state machine. `phase` can contain:

| Phase | Meaning |
|---|---|
| `loading` | Starting a run or preparing a restart |
| `playing` | A question is visible and answers are enabled |
| `answering` | The selected answer is being checked |
| `feedback` | Correct/wrong animation is playing |
| `gameover` | The final result overlay is visible |
| `error` | The API failed and the player can retry |

This is safer than managing many unrelated Boolean values. Only `playing` enables answer buttons, so repeated taps cannot submit multiple answers.

`phaseRef` mirrors the state value for immediate event-guard checks. React state updates are asynchronous, but a ref changes immediately. This closes the small window in which two very fast taps could both see the old phase.

### Starting and restarting

`startGame()` calls the start endpoint, stores the run UUID, score, best score, and time limit, then calls `beginQuestion()`.

The same function powers both the initial load and the **Play again** button.

### The countdown

The client stores an absolute deadline:

```ts
deadlineRef.current = Date.now() + timeLimitRef.current;
```

A short interval calculates the remaining duration from that deadline. This is more accurate than subtracting 50 milliseconds per interval, because browsers may delay timers when busy.

At zero, Ionic submits a `null` choice. Django still makes the final timeout decision.

### Answer feedback

After Django responds:

- The selected answer is remembered.
- Django's `correctChoiceId` identifies the green answer.
- A wrong selected answer becomes red and shakes.
- A correct answer becomes green and pulses.
- Buttons remain locked during feedback.
- A correct run advances after 900 milliseconds.
- A failed run opens the result overlay after 650 milliseconds.

The short delays give the player enough time to understand the outcome without removing the mode's rushed feeling.

## 9. Sound and haptic feedback

`feedback.ts` uses the browser Web Audio API to synthesize lightweight effects without downloading audio files:

- Correct: a rising three-note tone.
- Wrong: a lower descending/error tone.

Capacitor Haptics adds native mobile feedback:

- `NotificationType.Success` for a correct answer.
- `NotificationType.Error` for a wrong answer or timeout.

Both features fail gracefully. A browser without Web Audio or a device without haptics can still play the game.

## 10. Visual design and accessibility

The Top Score stylesheet provides:

- A score, best-score, and timer HUD.
- A continuously shrinking timer bar.
- A red pulsing timer during the final three seconds.
- Two-column answers on wider screens and one-column answers on phones.
- Correct and wrong animations.
- A blurred full-screen result overlay.
- Safe-area-aware layout through the shared `GameSubpage`.
- Reduced-animation behavior for `prefers-reduced-motion` users.

Accessibility details include:

- Native `<button>` elements for answers.
- A labelled answer group.
- Disabled controls when an answer is locked.
- `aria-live` updates.
- A modal result dialog with a labelled heading.
- A text label for the remaining time.

The topic catalogue was also restored to include its heading, topic count, introduction, and selected-topic announcement. This removed unused variables while keeping its existing component test and accessibility behavior intact.

## 11. Django admin

All quiz models are registered in Django admin:

- Topics can be searched, ordered, and activated.
- Questions can be filtered by topic, difficulty, and active status.
- Choices are editable inline with questions.
- Runs show player, score, status, reason, and timestamps.
- Responses show question order, correctness, and response time.

For question editing, keep this workflow in mind:

1. Create the question as inactive.
2. Save it.
3. Add exactly four choices with one correct answer.
4. Activate the question.

## 12. Migrations

Migrations are Django's version-controlled database changes.

The two quiz migrations are:

- `0001_initial.py`: creates topics, questions, choices, runs, responses, indexes, and constraints.
- `0002_*.py`: adds `current_question` and `question_started_at`, and allows reuse after the question bank is exhausted.

Apply migrations with:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

The development database was migrated while implementing this feature.

## 13. Tests and verification

The Django suite covers:

- Required question categories.
- Four-choice activation rules.
- Rejection of fifth or second-correct choices.
- Server-derived correctness.
- Rejection of a choice from another question.
- Timeout storage.
- Completed-run metadata.
- Idempotent seed data.
- Authentication requirement.
- Safe start payloads.
- Correct-answer score increments.
- Wrong-answer termination.
- Timeout termination.

The completed validation was:

```text
27 Django tests passed
11 Ionic tests passed
ESLint passed
TypeScript passed
Ionic production build passed
Django system check passed
No missing migrations
```

Useful commands:

```powershell
# Run Django tests
.\.venv\Scripts\python.exe manage.py test quiz accounts

# Run Ionic tests
npm run test -w @mind-clash/client

# Lint Ionic code
npm run lint -w @mind-clash/client

# Build Ionic production assets
npm run build -w @mind-clash/client

# Check Django configuration
.\.venv\Scripts\python.exe manage.py check
```

## 14. Running the complete feature

From the repository root:

```powershell
npm run dev:network
```

This launches Django and Vite for local and LAN access. Then:

1. Open the shown Vite URL locally or on a phone connected to the same network.
2. Register or log in.
3. Open **VS Bot**.
4. Select **Top Score**.
5. Answer before the timer reaches zero.

If a fresh database has no questions, run the migration and seed commands before starting:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_quiz
```

## 15. Safe future extensions

The current structure is ready for:

- Filtering `_next_question()` by a chosen topic.
- Difficulty progression based on score.
- Global or country leaderboards.
- Daily challenges.
- Question explanations on the result screen.
- Downloaded offline question packs.
- Audio settings that disable generated effects.
- Analytics for difficult or frequently failed questions.

For fairness, future clients should continue sending only player intent. Correctness, official deadlines, score changes, and leaderboard results should remain server-controlled.
