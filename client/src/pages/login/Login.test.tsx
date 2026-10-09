import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import TestIonRouter from '../../test/TestIonRouter';
import { appRoutes } from '../../routing/routes';
import Login from './Login';
import Register from '../register/Register';

const renderFlow = () =>
  render(
    <TestIonRouter initialEntry={appRoutes.login}>
      <Routes>
        <Route path={appRoutes.login} element={<Login />} />
        <Route path={appRoutes.register} element={<Register />} />
      </Routes>
    </TestIonRouter>,
  );

afterEach(() => {
  vi.useRealTimers();
});

test('renders login fields without making an authentication request', () => {
  renderFlow();

  expect(screen.getByRole('region', { name: 'Login form' })).toBeDefined();
  expect(screen.queryByText('Return to the archive')).toBeNull();
  expect(screen.queryByText('Scholar access')).toBeNull();
  expect(document.querySelectorAll('ion-input.auth-input')).toHaveLength(2);

  fireEvent.submit(document.querySelector('form')!);

  expect(screen.getByRole('status')).toHaveTextContent(/account connection comes in the next backend step/i);
});

test('moves from login to the registration screen', () => {
  vi.useFakeTimers();
  renderFlow();

  const registrationButton = screen.getByText('Create an account').closest('ion-button');
  expect(registrationButton).not.toBeNull();
  fireEvent.click(registrationButton!);
  act(() => vi.advanceTimersByTime(200));

  expect(screen.getByRole('region', { name: 'Create account form' })).toBeDefined();
  expect(document.querySelectorAll('ion-input.auth-input')).toHaveLength(5);
});

test('filters countries by name and stores the selected country code', () => {
  vi.useFakeTimers();
  renderFlow();

  fireEvent.click(screen.getByText('Create an account').closest('ion-button')!);
  act(() => vi.advanceTimersByTime(200));

  const countryInput = document.querySelector('ion-input.country-combobox__input')!;
  fireEvent.focus(countryInput);
  fireEvent.input(countryInput, { target: { value: 'tuni' } });

  fireEvent.click(screen.getByRole('option', { name: /Tunisia TN/i }));

  expect(document.querySelector<HTMLInputElement>('input[name="country"]')?.value).toBe('TN');
});
