/** Tests the session profile cache, including malformed and unavailable storage. */
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { cacheUser, clearCachedUser, readCachedUser } from './storage';

/** Verifies cached profile persistence and safe behavior when storage is unavailable. */
beforeEach(() => localStorage.clear());

/** Restores storage methods and removes cached state between test cases. */
afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

/** Confirms only a profile payload is persisted for offline UI restoration. */
test('round trips the cached account profile without storing credentials', () => {
  const user = {
    id: 12,
    username: 'reader',
    email: 'reader@example.com',
    country: 'TN',
    isStaff: false,
  };

  cacheUser(user);

  expect(readCachedUser()).toEqual(user);
  expect(localStorage.getItem('clash-of-minds:authenticated-user')).not.toContain('password');
});

/** Confirms malformed local data does not crash session restoration. */
test('returns no profile and clears malformed cached JSON safely', () => {
  localStorage.setItem('clash-of-minds:authenticated-user', '{invalid');

  expect(readCachedUser()).toBeNull();
  clearCachedUser();
  expect(localStorage.getItem('clash-of-minds:authenticated-user')).toBeNull();
});

/** Confirms blocked browser storage cannot break authentication helpers. */
test('keeps cache helpers safe when browser storage throws', () => {
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => { throw new Error('blocked'); });

  expect(() => cacheUser({ id: 1, username: 'x', email: 'x@example.com', country: 'TN' })).not.toThrow();
  expect(readCachedUser()).toBeNull();
  expect(() => clearCachedUser()).not.toThrow();
});
