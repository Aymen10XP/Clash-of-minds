export type AuthUser = {
  id: number;
  username: string;
  email: string;
  country: string;
};

export type RegistrationData = {
  username: string;
  email: string;
  country: string;
  password: string;
  confirmPassword: string;
};

export type LoginData = {
  identity: string;
  password: string;
  rememberMe: boolean;
};

type ErrorPayload = {
  error?: string;
  errors?: Record<string, string[]>;
};

export class AuthApiError extends Error {
  readonly fieldErrors: Record<string, string[]>;

  constructor(message: string, fieldErrors: Record<string, string[]> = {}) {
    super(message);
    this.name = 'AuthApiError';
    this.fieldErrors = fieldErrors;
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

let csrfBootstrap: Promise<void> | null = null;

const ensureCsrfToken = async () => {
  if (getCookie('csrftoken')) return;

  csrfBootstrap ??= fetch('/api/auth/me/', {
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  }).then((response) => {
    if (!response.ok) throw new AuthApiError('Unable to initialize a secure session.');
  }).finally(() => {
    csrfBootstrap = null;
  });

  await csrfBootstrap;
};

const request = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');

  if (options.body) {
    headers.set('Content-Type', 'application/json');
  }

  const method = options.method?.toUpperCase() ?? 'GET';
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    await ensureCsrfToken();
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) throw new AuthApiError('Unable to initialize a secure session. Refresh and try again.');
    headers.set('X-CSRFToken', csrfToken);
  }

  const response = await fetch(`/api/auth/${path}/`, {
    ...options,
    credentials: 'same-origin',
    headers,
  });

  const payload = (await response.json().catch(() => ({}))) as ErrorPayload & T;

  if (!response.ok) {
    const fieldErrors = payload.errors ?? {};
    const firstFieldMessage = Object.values(fieldErrors).flat()[0];
    throw new AuthApiError(
      payload.error ?? firstFieldMessage ?? 'Authentication request failed.',
      fieldErrors,
    );
  }

  return payload;
};

export const fetchCurrentUser = async () => {
  return request<{ authenticated: boolean; user: AuthUser | null }>('me');
};

export const registerAccount = async (data: RegistrationData) => {
  return request<{ user: AuthUser }>('register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const loginAccount = async (data: LoginData) => {
  return request<{ user: AuthUser }>('login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const logoutAccount = async () => {
  await request<{ message: string }>('logout', { method: 'POST' });
};
