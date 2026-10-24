/** Covers auth route guards against anonymous, signed-in, staff, and loading session states. */
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test } from 'vitest';
import { AuthContext, type AuthContextValue } from './context';
import { PublicOnly, RequireAuth, RequireStaff } from './AuthGate';

/** Builds a deterministic auth context value for a requested test session. */
const createAuthValue = (status: AuthContextValue['status'], isStaff = false): AuthContextValue => ({
  status,
  user: status === 'authenticated'
    ? { id: 1, username: 'player', email: 'player@example.com', country: 'TN', isStaff }
    : null,
  register: async () => undefined,
  updateProfile: async () => undefined,
  login: async () => undefined,
  logout: async () => undefined,
});

/** Renders a guard inside router and auth providers so redirects can be observed. */
const renderGuardedRoute = (
  auth: AuthContextValue,
  guard: ReactNode,
  initialPath: string,
) => render(
  <AuthContext.Provider value={auth}>
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/protected" element={guard} />
        <Route path="/login" element={<p>Login destination</p>} />
        <Route path="/home" element={<p>Home destination</p>} />
      </Routes>
    </MemoryRouter>
  </AuthContext.Provider>,
);

/** Ensures anonymous visitors cannot see authenticated route content. */
test('redirects anonymous users away from protected routes to login', () => {
  renderGuardedRoute(createAuthValue('anonymous'), <RequireAuth><p>Protected content</p></RequireAuth>, '/protected');

  expect(screen.getByText('Login destination')).toBeInTheDocument();
  expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
});

/** Ensures signed-in visitors are sent away from public-only pages. */
test('redirects authenticated users away from public-only routes to home', () => {
  renderGuardedRoute(createAuthValue('authenticated'), <PublicOnly><p>Sign-in form</p></PublicOnly>, '/protected');

  expect(screen.getByText('Home destination')).toBeInTheDocument();
  expect(screen.queryByText('Sign-in form')).not.toBeInTheDocument();
});

/** Ensures the staff gate admits staff and redirects ordinary accounts. */
test('allows staff to open the protected staff route and redirects ordinary users home', () => {
  const staff = renderGuardedRoute(
    createAuthValue('authenticated', true),
    <RequireStaff><p>Admin tools</p></RequireStaff>,
    '/protected',
  );
  expect(screen.getByText('Admin tools')).toBeInTheDocument();
  staff.unmount();

  renderGuardedRoute(
    createAuthValue('authenticated', false),
    <RequireStaff><p>Admin tools</p></RequireStaff>,
    '/protected',
  );
  expect(screen.getByText('Home destination')).toBeInTheDocument();
  expect(screen.queryByText('Admin tools')).not.toBeInTheDocument();
});

/** Ensures route content waits until initial session resolution is complete. */
test('shows a session status while authentication is still loading', () => {
  renderGuardedRoute(createAuthValue('loading'), <RequireAuth><p>Protected content</p></RequireAuth>, '/protected');

  expect(screen.getByRole('status', { name: 'Checking session' })).toBeInTheDocument();
});
