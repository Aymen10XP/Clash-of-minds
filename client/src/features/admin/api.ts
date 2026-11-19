export type AdminUser = {
  id: number;
  username: string;
  email: string;
  country: string;
  isActive: boolean;
  isStaff: boolean;
};

export type NewQuestion = {
  topicSlug: string;
  prompt: string;
  explanation: string;
  difficulty: 'easy' | 'medium' | 'hard';
  choices: string[];
  correctChoiceIndex: number;
  isActive: boolean;
};

export type AdminDashboard = {
  indicators: {
    activeUsers: number;
    activeTopics: number;
    activeQuestions: number;
    matchesByStatus: Record<string, number>;
  };
  auditEvents: {
    id: number;
    actor: string | null;
    action: string;
    targetType: string;
    targetId: string;
    details: Record<string, unknown>;
    createdAt: string;
  }[];
};

const cookie = (name: string) => document.cookie
  .split(';')
  .map((part) => part.trim())
  .find((part) => part.startsWith(`${name}=`))
  ?.slice(name.length + 1) ?? '';

const request = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
  let csrf = cookie('csrftoken');
  if (options.method && options.method !== 'GET' && !csrf) {
    await fetch('/api/auth/me/', { credentials: 'same-origin' });
    csrf = cookie('csrftoken');
  }
  const response = await fetch(path, {
    ...options,
    credentials: 'same-origin',
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(csrf ? { 'X-CSRFToken': decodeURIComponent(csrf) } : {}),
      ...options.headers,
    },
  });
  const payload = await response.json().catch(() => ({})) as T & { error?: string };
  if (!response.ok) throw new Error(payload.error ?? 'Administrator request failed.');
  return payload;
};

export const fetchAdminUsers = () => request<{ users: AdminUser[] }>('/api/auth/admin/users/');

export const fetchAdminDashboard = (action = '') => request<AdminDashboard>(
  `/api/auth/admin/dashboard/${action ? `?action=${encodeURIComponent(action)}` : ''}`,
);

export const deactivateUser = (userId: number) => request<{ userId: number; isActive: false }>(
  `/api/auth/admin/users/${userId}/deactivate/`,
  { method: 'POST', body: '{}' },
);

export const createQuestion = (question: NewQuestion) => request<{ question: { id: number } }>(
  '/api/quiz/admin/questions/',
  { method: 'POST', body: JSON.stringify(question) },
);
