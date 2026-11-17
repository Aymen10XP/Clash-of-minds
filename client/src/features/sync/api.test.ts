/** Tests offline-result synchronization and queue retention on failed uploads. */
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { cacheUser } from '../auth/storage';
import { answerOfflineTopScore, cacheOfflineCatalog, pendingOfflineRuns, startOfflineTopScore } from '../quiz/offline';
import { getPendingRunCount, synchronizeOfflineRuns } from './api';

const user = { id: 23, username: 'sync-player', email: 'sync@example.com', country: 'TN' };
const fetchMock = vi.fn();

/** Prepares one offline result and isolates network calls for each sync scenario. */
beforeEach(() => {
  localStorage.clear();
  document.cookie = 'csrftoken=sync-token; path=/';
  cacheUser(user);
  cacheOfflineCatalog(user.id, {
    version: 'sync-test', timeLimitMs: 10_000, bestScore: 0,
    questions: [{
      id: 3,
      topic: { slug: 'history', title: 'History' },
      prompt: 'Question?', difficulty: 'easy', correctChoiceId: 30,
      choices: [{ id: 30, text: 'Correct' }, { id: 31, text: 'Wrong' }],
    }],
  });
  const run = startOfflineTopScore();
  answerOfflineTopScore(run.runId, run.question.id, 31);
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

/** Removes mocked globals and local run state after each sync scenario. */
afterEach(() => {
  localStorage.clear();
  document.cookie = 'csrftoken=; max-age=0; path=/';
  vi.unstubAllGlobals();
});

/** Confirms successful server acknowledgements clear a queued run. */
test('uploads queued offline runs and removes only server-acknowledged run ids', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ syncedRunIds: [pendingOfflineRuns(user.id)[0].runId], bestScore: 5 }),
  });

  expect(getPendingRunCount(user.id)).toBe(1);
  await expect(synchronizeOfflineRuns(user)).resolves.toBe(1);
  expect(fetchMock).toHaveBeenCalledWith('/api/quiz/offline/sync/', expect.objectContaining({
    method: 'POST',
    credentials: 'same-origin',
    headers: expect.objectContaining({ 'X-CSRFToken': 'sync-token' }),
  }));
  expect(getPendingRunCount(user.id)).toBe(0);
});

/** Confirms failed uploads remain available for a later retry. */
test('keeps queued runs when the server rejects synchronization', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: false,
    json: async () => ({ error: 'Session expired.' }),
  });

  await expect(synchronizeOfflineRuns(user)).rejects.toThrow('Session expired.');
  expect(getPendingRunCount(user.id)).toBe(1);
});
