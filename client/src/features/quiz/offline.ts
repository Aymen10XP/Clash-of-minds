import { readCachedUser } from '../auth/storage';
import type { QuizQuestion, TopScoreAnswer, TopScoreStart } from './api';

type OfflineQuestion = QuizQuestion & { correctChoiceId: number };

type OfflineCatalog = {
  version: string;
  timeLimitMs: number;
  bestScore: number;
  questions: OfflineQuestion[];
};

type OfflineAnswer = {
  questionId: number;
  choiceId: number | null;
  responseTimeMs: number;
};

type OfflineRun = {
  runId: string;
  topicSlug?: string;
  startedAt: string;
  questionStartedAt: number;
  currentQuestionId: number;
  score: number;
  answers: OfflineAnswer[];
};

type OfflineStore = {
  bestScore: number;
  activeRuns: Record<string, OfflineRun>;
  pendingRuns: Array<Omit<OfflineRun, 'questionStartedAt' | 'currentQuestionId'> & {
    endedAt: string;
  }>;
};

const catalogKey = (userId: number) => `clash-of-minds:offline-catalog:${userId}`;
const storeKey = (userId: number) => `clash-of-minds:offline-runs:${userId}`;

const currentUserId = () => {
  const user = readCachedUser();
  if (!user) throw new Error('Sign in while connected before playing offline.');
  return user.id;
};

const readJson = <T,>(key: string): T | null => {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) as T : null;
  } catch {
    return null;
  }
};

const readStore = (userId: number): OfflineStore => readJson<OfflineStore>(storeKey(userId)) ?? {
  bestScore: 0,
  activeRuns: {},
  pendingRuns: [],
};

const writeStore = (userId: number, store: OfflineStore) => {
  localStorage.setItem(storeKey(userId), JSON.stringify(store));
};

const publicQuestion = (question: OfflineQuestion): QuizQuestion => ({
  id: question.id,
  topic: question.topic,
  prompt: question.prompt,
  difficulty: question.difficulty,
  choices: [...question.choices].sort(() => Math.random() - 0.5),
});

const pickQuestion = (catalog: OfflineCatalog, run: Pick<OfflineRun, 'topicSlug' | 'answers'>) => {
  const eligible = catalog.questions.filter((question) => (
    !run.topicSlug || question.topic.slug === run.topicSlug
  ));
  if (!eligible.length) throw new Error('No cached questions are available for this category.');
  const usedIds = new Set(run.answers.map((answer) => answer.questionId));
  const unused = eligible.filter((question) => !usedIds.has(question.id));
  const pool = unused.length ? unused : eligible;
  return pool[Math.floor(Math.random() * pool.length)];
};

const makeRunId = () => {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (character) => {
    const random = Math.floor(Math.random() * 16);
    const value = character === 'x' ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
};

export const cacheOfflineCatalog = (userId: number, catalog: OfflineCatalog) => {
  localStorage.setItem(catalogKey(userId), JSON.stringify(catalog));
  const store = readStore(userId);
  store.bestScore = Math.max(store.bestScore, catalog.bestScore);
  writeStore(userId, store);
};

export const startOfflineTopScore = (topicSlug?: string): TopScoreStart => {
  const userId = currentUserId();
  const catalog = readJson<OfflineCatalog>(catalogKey(userId));
  if (!catalog?.questions.length) {
    throw new Error('Connect to the internet once to download questions for offline play.');
  }

  const store = readStore(userId);
  const shell = { topicSlug, answers: [] as OfflineAnswer[] };
  const question = pickQuestion(catalog, shell);
  const runId = makeRunId();
  store.activeRuns[runId] = {
    runId,
    topicSlug,
    startedAt: new Date().toISOString(),
    questionStartedAt: Date.now(),
    currentQuestionId: question.id,
    score: 0,
    answers: [],
  };
  writeStore(userId, store);
  return {
    runId,
    score: 0,
    bestScore: store.bestScore,
    timeLimitMs: catalog.timeLimitMs,
    question: publicQuestion(question),
  };
};

export const hasOfflineRun = (runId: string) => {
  const user = readCachedUser();
  return Boolean(user && readStore(user.id).activeRuns[runId]);
};

export const answerOfflineTopScore = (
  runId: string,
  questionId: number,
  choiceId: number | null,
): TopScoreAnswer => {
  const userId = currentUserId();
  const catalog = readJson<OfflineCatalog>(catalogKey(userId));
  const store = readStore(userId);
  const run = store.activeRuns[runId];
  const question = catalog?.questions.find((item) => item.id === questionId);
  if (!catalog || !run || !question || run.currentQuestionId !== questionId) {
    throw new Error('This offline run is no longer available.');
  }

  const elapsed = Math.max(0, Math.min(catalog.timeLimitMs, Date.now() - run.questionStartedAt));
  const timedOut = choiceId === null || elapsed >= catalog.timeLimitMs;
  const correct = !timedOut && choiceId === question.correctChoiceId;
  run.answers.push({ questionId, choiceId: timedOut ? null : choiceId, responseTimeMs: elapsed });

  if (correct) {
    run.score += 1;
    store.bestScore = Math.max(store.bestScore, run.score);
    const nextQuestion = pickQuestion(catalog, run);
    run.currentQuestionId = nextQuestion.id;
    run.questionStartedAt = Date.now() + 900;
    writeStore(userId, store);
    return {
      correct: true,
      timedOut: false,
      correctChoiceId: question.correctChoiceId,
      score: run.score,
      bestScore: store.bestScore,
      gameOver: false,
      question: publicQuestion(nextQuestion),
    };
  }

  delete store.activeRuns[runId];
  store.pendingRuns.push({
    runId: run.runId,
    topicSlug: run.topicSlug,
    startedAt: run.startedAt,
    endedAt: new Date().toISOString(),
    score: run.score,
    answers: run.answers,
  });
  writeStore(userId, store);
  return {
    correct: false,
    timedOut,
    correctChoiceId: question.correctChoiceId,
    score: run.score,
    bestScore: store.bestScore,
    gameOver: true,
    endReason: timedOut ? 'timeout' : 'wrong_answer',
  };
};

export const quitOfflineTopScore = (runId: string) => {
  const userId = currentUserId();
  const store = readStore(userId);
  const run = store.activeRuns[runId];
  if (!run) return;
  delete store.activeRuns[runId];
  if (run.answers.length) {
    store.pendingRuns.push({
      runId: run.runId,
      topicSlug: run.topicSlug,
      startedAt: run.startedAt,
      endedAt: new Date().toISOString(),
      score: run.score,
      answers: run.answers,
    });
  }
  writeStore(userId, store);
};

export const pendingOfflineRuns = (userId: number) => readStore(userId).pendingRuns;

export const removeSyncedRuns = (userId: number, runIds: string[], bestScore: number) => {
  const store = readStore(userId);
  const synced = new Set(runIds);
  store.pendingRuns = store.pendingRuns.filter((run) => !synced.has(run.runId));
  store.bestScore = Math.max(store.bestScore, bestScore);
  writeStore(userId, store);
};
