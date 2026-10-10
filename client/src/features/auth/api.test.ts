import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { loginAccount } from './api';

const fetchMock = vi.fn();

beforeEach(() => {
  document.cookie = 'csrftoken=; max-age=0; path=/';
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  document.cookie = 'csrftoken=; max-age=0; path=/';
  vi.unstubAllGlobals();
});

test('bootstraps a missing CSRF cookie before login', async () => {
  fetchMock.mockImplementationOnce(async () => {
    document.cookie = 'csrftoken=fresh-token; path=/';
    return { ok: true, json: async () => ({ authenticated: false, user: null }) };
  });
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      user: {
        id: 1,
        username: 'historian',
        email: 'historian@example.com',
        country: 'TN',
      },
    }),
  });

  await loginAccount({ identity: 'historian', password: 'password', rememberMe: false });

  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/me/');

  const loginHeaders = fetchMock.mock.calls[1][1]?.headers as Headers;
  expect(loginHeaders.get('X-CSRFToken')).toBe('fresh-token');
});
