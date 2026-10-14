import {
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';
import {
  fetchCurrentUser,
  loginAccount,
  logoutAccount,
  registerAccount,
} from './api';
import { AuthContext, type AuthContextValue, type AuthStatus } from './context';
import type { AuthUser } from './api';
import { cacheUser, clearCachedUser, readCachedUser } from './storage';

export const AuthProvider: React.FC<PropsWithChildren> = ({ children }) => {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let active = true;

    void fetchCurrentUser()
      .then((response) => {
        if (!active) return;
        setUser(response.user);
        setStatus(response.authenticated ? 'authenticated' : 'anonymous');
        if (response.user) cacheUser(response.user);
        else clearCachedUser();
      })
      .catch(() => {
        if (!active) return;
        const cachedUser = readCachedUser();
        setUser(cachedUser);
        setStatus(cachedUser ? 'authenticated' : 'anonymous');
      });

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      register: async (data) => {
        await registerAccount(data);
      },
      login: async (data) => {
        const response = await loginAccount(data);
        cacheUser(response.user);
        setUser(response.user);
        setStatus('authenticated');
      },
      logout: async () => {
        await logoutAccount();
        clearCachedUser();
        setUser(null);
        setStatus('anonymous');
      },
    }),
    [status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
