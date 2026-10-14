import type { AuthUser } from '../auth/api';
import {
  cacheOfflineCatalog,
  pendingOfflineRuns,
  removeSyncedRuns,
} from '../quiz/offline';

const getCookie = (name: string) => {
  const prefix = `${name}=`;
  const cookie = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix));
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : '';
};

export const refreshOfflineCatalog = async (user: AuthUser) => {
  const response = await fetch('/api/quiz/offline/catalog/', {
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error('Unable to refresh offline questions.');
  const catalog = await response.json();
  if (!Array.isArray(catalog.questions)) throw new Error('The offline question pack is invalid.');
  cacheOfflineCatalog(user.id, catalog);
};

export const getPendingRunCount = (userId: number) => pendingOfflineRuns(userId).length;

export const synchronizeOfflineRuns = async (user: AuthUser) => {
  if (!pendingOfflineRuns(user.id).length) return 0;

  if (!getCookie('csrftoken')) {
    const bootstrap = await fetch('/api/auth/me/', {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    });
    if (!bootstrap.ok) throw new Error('Unable to restore the secure session.');
  }

  let syncedCount = 0;
  while (pendingOfflineRuns(user.id).length) {
    const runs = pendingOfflineRuns(user.id).slice(0, 100);
    const response = await fetch('/api/quiz/offline/sync/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ runs }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error ?? 'Synchronization could not be completed.');
    removeSyncedRuns(user.id, payload.syncedRunIds, payload.bestScore);
    syncedCount += payload.syncedRunIds.length as number;
  }
  return syncedCount;
};
