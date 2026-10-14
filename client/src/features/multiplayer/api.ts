export type MultiplayerPlayer = { id: number; username: string; country: string };

export type MatchInvitation = {
  id: string;
  status: 'pending' | 'accepted' | 'declined' | 'cancelled';
  direction: 'incoming' | 'outgoing';
  sender: MultiplayerPlayer;
  recipient: MultiplayerPlayer;
  createdAt: string;
  respondedAt: string | null;
  matchId: string | null;
};

export type MatchParticipant = MultiplayerPlayer & {
  seat: 'host' | 'guest';
  score: number;
  hearts: number;
  ready: boolean;
  isCurrentUser: boolean;
};

export type MatchRound = {
  sequence: number;
  question: {
    id: number;
    topic: { slug: string; title: string };
    prompt: string;
    difficulty: 'easy' | 'medium' | 'hard';
    choices: Array<{ id: number; text: string }>;
  };
  hasAnswered: boolean;
  selectedChoiceId: number | null;
};

export type KnowledgeMatch = {
  id: string;
  status: 'waiting' | 'active' | 'completed' | 'cancelled';
  createdAt: string;
  startedAt: string | null;
  endedAt: string | null;
  endReason: 'hearts' | 'time' | null;
  winnerId: number | null;
  durationMs: number;
  remainingMs: number;
  participants: MatchParticipant[];
  currentRound: MatchRound | null;
  lastRound: {
    sequence: number;
    winnerId: number | null;
    correctChoiceId: number;
  } | null;
};

export class MultiplayerApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'MultiplayerApiError';
    this.status = status;
  }
}

const getCookie = (name: string) => {
  const prefix = `${name}=`;
  const cookie = document.cookie.split(';').map((part) => part.trim())
    .find((part) => part.startsWith(prefix));
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : '';
};

const request = async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
  const method = options.method?.toUpperCase() ?? 'GET';
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && !getCookie('csrftoken')) {
    await fetch('/api/auth/me/', { credentials: 'same-origin', headers: { Accept: 'application/json' } });
  }
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  if (options.body) headers.set('Content-Type', 'application/json');
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    headers.set('X-CSRFToken', getCookie('csrftoken'));
  }
  const response = await fetch(`/api/multiplayer/${path}`, {
    ...options,
    credentials: 'same-origin',
    headers,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new MultiplayerApiError(payload.error ?? 'The multiplayer service did not respond.', response.status);
  }
  return payload as T;
};

const post = <T,>(path: string, body: object = {}) => request<T>(path, {
  method: 'POST',
  body: JSON.stringify(body),
});

export const searchMultiplayerPlayers = async (query: string) => (
  request<{ players: MultiplayerPlayer[] }>(`players/?q=${encodeURIComponent(query)}`)
).then((payload) => payload.players);

export const fetchInvitations = async () => (
  request<{ invitations: MatchInvitation[] }>('invitations/')
).then((payload) => payload.invitations);

export const sendMatchInvitation = async (recipientId: number) => (
  post<{ invitation: MatchInvitation }>('invitations/send/', { recipientId })
).then((payload) => payload.invitation);

export const respondToMatchInvitation = async (invitationId: string, action: 'accept' | 'decline') => (
  post<{ invitation: MatchInvitation; match: KnowledgeMatch | null }>(
    `invitations/${invitationId}/respond/`,
    { action },
  )
);

export const cancelMatchInvitation = async (invitationId: string) => (
  post<{ invitation: MatchInvitation }>(`invitations/${invitationId}/cancel/`)
).then((payload) => payload.invitation);

export const fetchMatches = async () => (
  request<{ matches: KnowledgeMatch[] }>('matches/')
).then((payload) => payload.matches);

export const fetchMatch = async (matchId: string) => (
  request<{ match: KnowledgeMatch }>(`matches/${matchId}/`)
).then((payload) => payload.match);

export const markMatchReady = async (matchId: string) => (
  post<{ match: KnowledgeMatch }>(`matches/${matchId}/ready/`)
).then((payload) => payload.match);

export const submitMatchAnswer = async (matchId: string, questionId: number, choiceId: number) => (
  post<{ match: KnowledgeMatch }>(`matches/${matchId}/answer/`, { questionId, choiceId })
).then((payload) => payload.match);
