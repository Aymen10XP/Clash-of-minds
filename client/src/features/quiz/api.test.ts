/** Tests online and cached/offline behavior of the quiz API adapter. */
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { cacheUser } from '../auth/storage';
import { startTopScore } from './api';

/** Exercises online, offline, and API-error behavior of the Top Score client. */
const fetchMock = vi.fn();

/** Resets browser state so each quiz API test owns its own request setup. */
beforeEach(() => {
  localStorage.clear();
  document.cookie = 'csrftoken=; max-age=0; path=/';
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  vi.stubGlobal('navigator', { ...navigator, onLine: true });
});

/** Removes test-only globals and cookies after each quiz API scenario. */
afterEach(() => {
  localStorage.clear();
  document.cookie = 'csrftoken=; max-age=0; path=/';
  vi.unstubAllGlobals();
});

/** Verifies that online runs include the selected topic and session credentials. */
test('starts an online Top Score run with the requested topic', async () => {
  document.cookie = 'csrftoken=quiz-token; path=/';
  const run = {
    runId: 'online-run',
    score: 0,
    bestScore: 4,
    timeLimitMs: 10_000,
    question: {
      id: 7,
      topic: { slug: 'history', title: 'History' },
      prompt: 'Question?',
      difficulty: 'easy',
      choices: [{ id: 1, text: 'Answer' }],
    },
  };
  fetchMock.mockResolvedValueOnce({ ok: true, json: async () => run });

  await expect(startTopScore('history')).resolves.toEqual(run);

  expect(fetchMock).toHaveBeenCalledWith('/api/quiz/top-score/start/', expect.objectContaining({
    method: 'POST',
    credentials: 'same-origin',
    body: JSON.stringify({ topicSlug: 'history' }),
  }));
});

/** Verifies that an offline device starts from its cached question catalogue. */
test('starts from cached questions when the device is offline', async () => {
  cacheUser({ id: 8, username: 'player', email: 'p@example.com', country: 'TN' });
  vi.stubGlobal('navigator', { ...navigator, onLine: false });
  localStorage.setItem('clash-of-minds:offline-catalog:8', JSON.stringify({
    version: '1', timeLimitMs: 10_000, bestScore: 2,
    questions: [{
      id: 4,
      topic: { slug: 'science', title: 'Science' },
      prompt: 'Cached question?', difficulty: 'easy', correctChoiceId: 40,
      choices: [{ id: 40, text: 'Yes' }, { id: 41, text: 'No' }],
    }],
  }));

  const run = await startTopScore('science');

  expect(run.runId).toBeTruthy();
  expect(run.question.id).toBe(4);
  expect(fetchMock).not.toHaveBeenCalled();
});

/** Verifies server validation failures remain visible instead of triggering fallback. */
test('does not hide an online API validation error by switching to offline play', async () => {
  document.cookie = 'csrftoken=quiz-token; path=/';
  fetchMock.mockResolvedValueOnce({
    ok: false,
    status: 400,
    json: async () => ({ error: 'Unknown topic.' }),
  });

  await expect(startTopScore('missing')).rejects.toThrow('Unknown topic.');
});
