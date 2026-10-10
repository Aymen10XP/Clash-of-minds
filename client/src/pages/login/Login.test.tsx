import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import TestIonRouter from '../../test/TestIonRouter';
import { appRoutes } from '../../routing/routes';
import Login from './Login';
import Register from '../register/Register';
import { AuthProvider } from '../../features/auth/AuthContext';

const fetchMock = vi.fn();

const jsonResponse = (body: unknown, ok = true) => ({
  ok,
  json: async () => body,
});

const renderFlow = () =>
  render(
    <TestIonRouter initialEntry={appRoutes.login}>
      <AuthProvider>
        <Routes>
          <Route path={appRoutes.login} element={<Login />} />
          <Route path={appRoutes.register} element={<Register />} />
        </Routes>
      </AuthProvider>
    </TestIonRouter>,
  );

beforeEach(() => {
  document.cookie = 'csrftoken=test-csrf-token; path=/';
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockReset();
  fetchMock.mockResolvedValueOnce(jsonResponse({ authenticated: false, user: null }));
});

afterEach(() => {
  document.cookie = 'csrftoken=; max-age=0; path=/';
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

test('renders login fields and reports rejected credentials', async () => {
  fetchMock.mockResolvedValueOnce(jsonResponse({ error: 'Invalid username, email, or password.' }, false));
  renderFlow();

  expect(await screen.findByRole('region', { name: 'Login form' })).toBeDefined();
  expect(screen.queryByText('Return to the archive')).toBeNull();
  expect(screen.queryByText('Scholar access')).toBeNull();
  expect(document.querySelectorAll('ion-input.auth-input')).toHaveLength(2);

  fireEvent.submit(document.querySelector('form')!);

  expect(await screen.findByRole('alert')).toHaveTextContent(/invalid username, email, or password/i);
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

test('moves from login to the registration screen', async () => {
  renderFlow();

  const registrationButton = (await screen.findByText('Create an account')).closest('ion-button');
  expect(registrationButton).not.toBeNull();
  fireEvent.click(registrationButton!);

  expect(await screen.findByRole('region', { name: 'Create account form' })).toBeDefined();
  expect(document.querySelectorAll('ion-input.auth-input')).toHaveLength(5);
});

test('filters countries by name and stores the selected country code', async () => {
  renderFlow();

  fireEvent.click((await screen.findByText('Create an account')).closest('ion-button')!);
  await screen.findByRole('region', { name: 'Create account form' });

  const countryInput = document.querySelector('ion-input.country-combobox__input')!;
  fireEvent.focus(countryInput);
  fireEvent.input(countryInput, { target: { value: 'tuni' } });

  fireEvent.click(screen.getByRole('option', { name: /Tunisia TN/i }));

  expect(document.querySelector<HTMLInputElement>('input[name="country"]')?.value).toBe('TN');
});
