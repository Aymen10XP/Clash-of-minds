/** k6 load scenario for the authenticated multiplayer player-search endpoint. */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const baseUrl = (__ENV.BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const identity = __ENV.DEMO_PLAYER_USERNAME || 'demo_player';
const password = __ENV.DEMO_PLAYER_PASSWORD;
const searchDuration = new Trend('player_search_duration', true);
const searchFailures = new Rate('player_search_failures');
let authenticated = false;

export const options = {
  vus: Number(__ENV.VUS || 20),
  duration: __ENV.DURATION || '1m',
  // k6 normally clears cookies after every iteration; keep each VU signed in.
  noCookiesReset: true,
  thresholds: {
    player_search_duration: ['p(95)<500'],
    player_search_failures: ['rate<0.01'],
  },
};

/** Lets a new Docker network route settle before virtual users bootstrap sessions. */
export function setup() {
  sleep(1);
}

/** Authenticates each virtual user once, then measures repeated player searches. */
export default function playerSearchLoadScenario() {
  const jar = http.cookieJar();
  if (!authenticated) {
    if (!password) throw new Error('Set DEMO_PLAYER_PASSWORD before running the load check.');
    // Avoid turning the development server's small accept queue into a login-spike test.
    sleep((__VU - 1) * 0.05);

    let csrfToken;
    let sessionStatus = 0;
    for (let attempt = 0; attempt < 5; attempt += 1) {
      const sessionCheck = http.get(`${baseUrl}/api/auth/me/`);
      sessionStatus = sessionCheck.status;
      csrfToken = jar.cookiesForURL(baseUrl).csrftoken?.[0];
      if (sessionStatus === 200 && csrfToken) break;
      sleep(0.2);
    }
    if (!csrfToken) throw new Error(`Demo session bootstrap failed (GET ${sessionStatus}).`);
    const login = http.post(
      `${baseUrl}/api/auth/login/`,
      JSON.stringify({ identity, password, rememberMe: true }),
      {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
      },
    );
    const loggedIn = check(login, { 'demo account login succeeds': (response) => response.status === 200 });
    if (!loggedIn) {
      throw new Error(`Demo login failed after session bootstrap (GET ${sessionStatus}, POST ${login.status}).`);
    }
    authenticated = true;
  }

  const response = http.get(`${baseUrl}/api/multiplayer/players/?q=demo`);
  searchDuration.add(response.timings.duration);
  const succeeded = check(response, {
    'player search returns HTTP 200': (result) => result.status === 200,
    'player search returns a players list': (result) => {
      try { return Array.isArray(result.json('players')); } catch { return false; }
    },
  });
  searchFailures.add(!succeeded);
  sleep(1);
}
