# Authentication System Guide

This guide explains the Clash of Minds authentication system from the beginning. It is written for someone new to Django and shows how Django, PostgreSQL, and the Ionic React client work together.

## 1. What the system supports

The current authentication system allows a player to:

- Register with a username, email address, country, and password.
- Sign in with either a username or an email address.
- Choose whether the session should end when the browser closes.
- Refresh the application without losing an active session.
- Sign out from the main menu.
- Access the main menu and game routes only after signing in.

The API has four endpoints:

| Method | URL | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register/` | Create an account |
| `POST` | `/api/auth/login/` | Verify credentials and start a session |
| `POST` | `/api/auth/logout/` | End the current session |
| `GET` | `/api/auth/me/` | Return the current user and initialize CSRF protection |

## 2. The main Django concepts

### User model

Django represents every account with a user model. Clash of Minds defines its user in `accounts/models.py`:

```python
class User(AbstractUser):
    email = models.EmailField(unique=True)
    country = models.CharField(max_length=2, validators=[country_code_validator])
```

`AbstractUser` gives us Django's standard account fields and behavior:

- Username
- Password hash
- First and last name
- Active/staff/superuser flags
- Groups and permissions
- Login metadata

We extend it with a unique email address and a two-letter country code.

The setting below tells Django to use this model instead of its default user model:

```python
AUTH_USER_MODEL = 'accounts.User'
```

This is configured in `server/settings.py`.

### Password hashing

Django does not store the original password. It stores a salted, one-way password hash containing the algorithm and parameters required to check future login attempts.

The registration form eventually calls:

```python
user.set_password(raw_password)
```

During login, Django hashes the submitted password with the stored settings and compares the result safely. The application never needs to decrypt a password, and no API response returns the password field.

Never create a password like this:

```python
user.password = raw_password
```

That would store unsafe plain text. Use `UserCreationForm`, `create_user()`, or `set_password()` instead.

### Authentication and sessions

Authentication answers: "Are these credentials valid?"

```python
user = authenticate(request, username=username, password=password)
```

If the credentials are valid, Django returns the user. Otherwise, it returns `None`.

A session remembers the authenticated user between requests:

```python
login(request, user)
```

`login()` stores the user's ID in the Django session and sends the browser a session cookie. The cookie contains a session identifier, not the user's password.

On later requests, `AuthenticationMiddleware` reads that session and provides:

```python
request.user
```

If there is no authenticated session, `request.user` is an anonymous user.

Signing out clears the session:

```python
logout(request)
```

## 3. Backend structure

### Registration form

File: `accounts/forms.py`

`RegistrationForm` extends Django's `UserCreationForm`:

```python
class RegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'country')
```

`UserCreationForm` provides:

- `password1` and `password2` fields.
- Password matching validation.
- Django password-strength validation.
- Username validation.
- Secure password hashing when the form is saved.

Our form also:

- Converts email addresses to lowercase.
- Rejects an email already used with different capitalization.
- Converts country codes to uppercase.

### JSON helpers

File: `accounts/views.py`

The Ionic application sends JSON instead of an HTML form submission. `_read_json()` converts the request body into a Python dictionary and rejects malformed JSON or a JSON value that is not an object.

`_form_errors()` converts Django form errors into JSON that the Ionic application can display.

`_user_payload()` defines the only user fields returned to the client:

```json
{
  "id": 1,
  "username": "historian",
  "email": "historian@example.com",
  "country": "TN"
}
```

Keeping this mapping explicit prevents private fields such as the password hash from accidentally appearing in an API response.

## 4. Registration flow

The Ionic client sends:

```json
{
  "username": "historian",
  "email": "historian@example.com",
  "country": "TN",
  "password": "a-strong-password",
  "confirmPassword": "a-strong-password"
}
```

The registration view maps the client field names to Django's form names:

```python
form = RegistrationForm({
    'username': data.get('username', ''),
    'email': data.get('email', ''),
    'country': data.get('country', ''),
    'password1': data.get('password', ''),
    'password2': data.get('confirmPassword', ''),
})
```

When the form is valid, `form.save()` creates the user and hashes the password. The endpoint returns HTTP `201 Created`.

When validation fails, it returns HTTP `400 Bad Request` with field errors:

```json
{
  "errors": {
    "password2": ["The two password fields didn't match."]
  }
}
```

Registration does not automatically sign the player in. After successful registration, Ionic redirects to the login page and displays a confirmation message.

## 5. Login flow

The client sends:

```json
{
  "identity": "historian@example.com",
  "password": "a-strong-password",
  "rememberMe": true
}
```

The login view supports username or email:

1. If the identity contains `@`, Django searches for the email case-insensitively.
2. It gets the matching username.
3. It calls Django's `authenticate()` with the username and password.
4. It calls `login()` when authentication succeeds.

Invalid credentials return one generic error:

```json
{
  "error": "Invalid username, email, or password."
}
```

The generic message avoids revealing whether a particular username or email exists.

When `rememberMe` is false, the session expires when the browser closes:

```python
request.session.set_expiry(0)
```

When it is true, Django uses its normal session lifetime.

## 6. Current-user flow

When Ionic starts, `AuthProvider` requests:

```text
GET /api/auth/me/
```

An authenticated response looks like:

```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "historian",
    "email": "historian@example.com",
    "country": "TN"
  }
}
```

An anonymous response looks like:

```json
{
  "authenticated": false,
  "user": null
}
```

This endpoint also uses `ensure_csrf_cookie`, so the browser receives the CSRF cookie needed for registration, login, and logout.

## 7. CSRF protection

CSRF means Cross-Site Request Forgery. Without protection, another website could try to make a state-changing request using a player's active session.

Django's `CsrfViewMiddleware` requires unsafe requests such as `POST` to provide a valid CSRF token.

The client flow is:

1. Request `/api/auth/me/`.
2. Django sets the `csrftoken` cookie.
3. The client reads that cookie.
4. The client sends it in the `X-CSRFToken` header on every `POST` request.
5. Django checks the cookie, header, host, and request origin.

If the client was opened before Django started, the initial `/me/` request could not set a cookie. The API helper therefore checks for the cookie before every unsafe request and automatically repeats the `/me/` bootstrap if necessary.

For phone testing, the combined development script detects the computer's network addresses and supplies them to Django through:

- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

This allows requests from the Vite network URL without disabling Django's CSRF protection.

Do not solve CSRF errors by adding `csrf_exempt` to the authentication views. That would remove an important security layer.

## 8. Frontend structure

### API helper

File: `client/src/features/auth/api.ts`

This module:

- Sends requests to `/api/auth/...`.
- Sends and receives cookies with the same origin.
- Adds the JSON content type.
- Adds `X-CSRFToken` to unsafe requests.
- Bootstraps a missing CSRF cookie.
- Converts failed responses into `AuthApiError` objects.
- Defines TypeScript types for users and request data.

### Authentication context

Files:

- `client/src/features/auth/AuthContext.tsx`
- `client/src/features/auth/context.ts`

`AuthProvider` stores the global authentication state:

```text
loading -> checking /me/
authenticated -> a user session exists
anonymous -> no user session exists
```

It also provides `register()`, `login()`, and `logout()` functions to components through the `useAuth()` hook.

The provider is mounted in `client/src/App.tsx`, so the whole application shares one source of authentication state.

### Route guards

File: `client/src/features/auth/AuthGate.tsx`

`RequireAuth` protects the main menu and game routes:

```text
loading       -> show the session loading screen
anonymous     -> redirect to /login
authenticated -> render the requested page
```

`PublicOnly` protects the login and registration routes in the opposite direction. An authenticated player who opens `/login` or `/register` is redirected to `/home`.

The route rules are applied in `client/src/routing/GameRouter.tsx`.

The guards prevent the main menu from being rendered while the session is unknown or anonymous, so protected content does not flash briefly during startup.

Client-side route guards improve navigation and user experience, but future private Django API endpoints must also check authentication on the server. A React guard is not a replacement for backend authorization.

### Login and registration pages

Files:

- `client/src/pages/login/Login.tsx`
- `client/src/pages/register/Register.tsx`
- `client/src/components/auth/AuthPage.tsx`

`AuthPage` owns common form behavior:

- Prevent normal browser form submission.
- Disable the button while waiting.
- Display server errors.
- Display success notices.

The login and registration pages convert their existing Ionic form values into typed API requests.

### Logout

The account button in `client/src/pages/home/Home.tsx` now calls `logout()`. Django clears the session, the context changes to `anonymous`, and `RequireAuth` redirects the player to `/login`.

## 9. Vite proxy and development networking

File: `client/vite.config.ts`

During development, Ionic requests `/api/...` from the same Vite origin. Vite proxies those requests to:

```text
http://127.0.0.1:8000
```

The browser therefore communicates with one visible origin, while Vite forwards API traffic to Django.

The combined launcher is `scripts/dev-network.mjs`. Run it from the repository root:

```powershell
npm run dev:network
```

It starts:

- Vite at `0.0.0.0:5173`.
- Django at `0.0.0.0:8000`.
- Local URLs for development on the computer.
- Network URLs for testing on a phone.

It also prints the detected URLs. Press `Ctrl+C` once to stop both processes.

PostgreSQL must be running first:

```powershell
npm run db:up
```

## 10. URL wiring

`accounts/urls.py` defines the four authentication paths. `server/urls.py` includes them under:

```python
path('api/auth/', include('accounts.urls'))
```

Keeping app URLs inside `accounts/urls.py` makes the accounts application self-contained and prevents the project URL file from becoming crowded.

## 11. Tests

Backend tests are in `accounts/tests.py`. They verify:

- Passwords are hashed rather than stored as plain text.
- Email addresses are unique.
- Country codes are validated.
- Registration creates the expected user.
- Registration errors are returned as JSON.
- Username login works.
- Case-insensitive email login works.
- Invalid credentials are rejected.
- Browser-close and remembered sessions behave differently.
- `/me/` reports anonymous and authenticated states.
- `/me/` sets the CSRF cookie.
- Logout clears the session.
- A CSRF-protected login rejects a missing token and accepts a valid token.

Run backend tests with:

```powershell
npm run test -w @mind-clash/server
```

Frontend authentication tests verify:

- Anonymous users are redirected before the menu renders.
- Authenticated users can see the menu.
- Login errors appear in the form.
- Login and registration navigation works.
- Country selection stores the country code.
- A missing CSRF cookie is bootstrapped before login.

Run the focused frontend tests with:

```powershell
npm run test -w @mind-clash/client -- --run src/features/auth/api.test.ts src/App.test.tsx src/pages/login/Login.test.tsx
```

Build the client with:

```powershell
npm run build -w @mind-clash/client
```

Check Django configuration with:

```powershell
npm run check -w @mind-clash/server
```

## 12. Troubleshooting

### Registration or login returns HTTP 403

This normally means Django rejected the CSRF token or request origin.

Check that:

1. Django is running before submitting the form.
2. The application was started with `npm run dev:network` for phone testing.
3. `/api/auth/me/` returns HTTP 200.
4. The browser has a `csrftoken` cookie.
5. The POST request contains the `X-CSRFToken` header.

Do not disable CSRF protection.

### The phone cannot open the client

- Connect the phone and computer to the same network.
- Use the `Client network` URL printed by the script.
- Allow Node through the Windows firewall if prompted.
- Make sure no other process occupies port `5173`.

### Django cannot start

- Start PostgreSQL with `npm run db:up`.
- Confirm that `server/.env` exists.
- Confirm that the PostgreSQL settings match `compose.yaml`.
- Make sure port `8000` is free.

### The menu redirects to login

This is expected when `/api/auth/me/` reports no active session. Sign in again. If a remembered session unexpectedly disappears, inspect the browser cookies and the Django session database.

## 13. Important security rules for future work

- Never store or log raw passwords.
- Never return password hashes through the API.
- Keep CSRF protection enabled for session-authenticated requests.
- Use HTTPS and secure cookies in production.
- Protect every private backend endpoint, not only the React route.
- Add login throttling before exposing the application publicly.
- Keep `DJANGO_SECRET_KEY` private.
- Set `DJANGO_DEBUG=False` in production.
- Use explicit production hosts and trusted origins instead of broad wildcards.

This implementation intentionally uses Django sessions instead of JWT tokens. Sessions are simpler for this first-party web application, keep authentication tokens out of browser storage, and use Django's built-in security and session invalidation behavior.
