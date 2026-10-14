import type { AuthUser } from './api';

const CACHED_USER_KEY = 'clash-of-minds:authenticated-user';

export const readCachedUser = (): AuthUser | null => {
  try {
    const value = localStorage.getItem(CACHED_USER_KEY);
    return value ? JSON.parse(value) as AuthUser : null;
  } catch {
    return null;
  }
};

export const cacheUser = (user: AuthUser) => {
  try {
    localStorage.setItem(CACHED_USER_KEY, JSON.stringify(user));
  } catch {
    // Online authentication remains usable if device storage is unavailable.
  }
};

export const clearCachedUser = () => {
  try {
    localStorage.removeItem(CACHED_USER_KEY);
  } catch {
    // There is nothing else to clear when device storage is unavailable.
  }
};
