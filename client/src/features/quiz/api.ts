export type QuizChoice = { id: number; text: string };

export type QuizQuestion = {
  id: number;
  topic: { slug: string; title: string };
  prompt: string;
  difficulty: 'easy' | 'medium' | 'hard';
  choices: QuizChoice[];
};

export type TopScoreStart = {
  runId: string;
  score: number;
  bestScore: number;
  timeLimitMs: number;
  question: QuizQuestion;
};

export type TopScoreAnswer = {
  correct: boolean;
  timedOut: boolean;
  correctChoiceId: number;
  score: number;
  bestScore: number;
  gameOver: boolean;
  endReason?: 'wrong_answer' | 'timeout';
  question?: QuizQuestion;
};

export class QuizApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'QuizApiError';
  }
}

const getCookie = (name: string) => {
  const prefix = `${name}=`;
  const cookie = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix));
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : '';
};

const post = async <T>(path: string, body: object = {}): Promise<T> => {
  if (!getCookie('csrftoken')) {
    const bootstrap = await fetch('/api/auth/me/', {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    });
    if (!bootstrap.ok) throw new QuizApiError('Unable to initialize a secure game session.');
  }

  const response = await fetch(`/api/quiz/${path}`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify(body),
  });
  const payload = (await response.json().catch(() => ({}))) as T & { error?: string };
  if (!response.ok) throw new QuizApiError(payload.error ?? 'The game server did not respond.');
  return payload;
};

export const startTopScore = () => post<TopScoreStart>('top-score/start/');

export const answerTopScore = (
  runId: string,
  questionId: number,
  choiceId: number | null,
) => post<TopScoreAnswer>(`top-score/${runId}/answer/`, { questionId, choiceId });

export const quitTopScore = async (runId: string) => {
  await post<{ message: string }>(`top-score/${runId}/quit/`);
};
