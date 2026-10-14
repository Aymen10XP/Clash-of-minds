import { beforeEach, expect, test, vi } from 'vitest';
import { cacheUser } from '../auth/storage';
import {
  answerOfflineTopScore,
  cacheOfflineCatalog,
  pendingOfflineRuns,
  startOfflineTopScore,
} from './offline';

const user = {
  id: 42,
  username: 'offline-player',
  email: 'offline@example.com',
  country: 'TN',
};

beforeEach(() => {
  localStorage.clear();
  cacheUser(user);
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-10-14T12:00:00Z'));
  cacheOfflineCatalog(user.id, {
    version: 'test',
    timeLimitMs: 10_000,
    bestScore: 3,
    questions: [1, 2].map((id) => ({
      id,
      topic: { slug: 'history', title: 'History' },
      prompt: `Question ${id}`,
      difficulty: 'easy' as const,
      correctChoiceId: id * 10,
      choices: [
        { id: id * 10, text: 'Correct' },
        { id: id * 10 + 1, text: 'Wrong' },
      ],
    })),
  });
});

test('plays from the cached catalogue and queues a server-verifiable result', () => {
  const started = startOfflineTopScore('history');
  const firstCorrectId = started.question.id * 10;
  const correct = answerOfflineTopScore(started.runId, started.question.id, firstCorrectId);

  expect(correct.correct).toBe(true);
  expect(correct.score).toBe(1);
  expect(correct.bestScore).toBe(3);

  vi.advanceTimersByTime(2_000);
  const secondQuestion = correct.question!;
  const wrong = answerOfflineTopScore(
    started.runId,
    secondQuestion.id,
    secondQuestion.id * 10 + 1,
  );

  expect(wrong.gameOver).toBe(true);
  expect(wrong.endReason).toBe('wrong_answer');
  expect(pendingOfflineRuns(user.id)).toHaveLength(1);
  expect(pendingOfflineRuns(user.id)[0].answers).toHaveLength(2);
});
