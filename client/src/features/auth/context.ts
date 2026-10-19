import { createContext, useContext } from 'react';
import type { AuthUser, LoginData, ProfileUpdateData, RegistrationData } from './api';

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous';

export type AuthContextValue = {
  status: AuthStatus;
  user: AuthUser | null;
  register: (data: RegistrationData) => Promise<void>;
  updateProfile: (data: ProfileUpdateData) => Promise<void>;
  login: (data: LoginData) => Promise<void>;
  logout: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider.');
  return context;
};
