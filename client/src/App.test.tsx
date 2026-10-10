import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';
import App from './App';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  fetchMock.mockResolvedValue({
    ok: true,
    json: async () => ({
      authenticated: true,
      user: {
        id: 1,
        username: 'historian',
        email: 'historian@example.com',
        country: 'TN',
      },
    }),
  });
  vi.stubGlobal('fetch', fetchMock);
  vi.spyOn(window.HTMLMediaElement.prototype, 'play').mockResolvedValue();
  vi.spyOn(window.HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

test('renders the main game menu', async () => {
  render(<App />);

  expect(await screen.findByRole('img', { name: /clash of minds/i })).toBeDefined();
  expect(screen.getByText('Story Mode')).toBeDefined();
  expect(screen.getByText('VS Bot')).toBeDefined();
  expect(screen.getByText('Multiplayer')).toBeDefined();
  expect(screen.getByText('Settings')).toBeDefined();

  const storyButton = screen.getByText('Story Mode').closest('ion-button');
  expect(storyButton).not.toBeNull();
  fireEvent.click(storyButton!);
  expect(storyButton?.classList.contains('menu-button--selected')).toBe(true);
});

test('redirects anonymous visitors to login without rendering the menu', async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ authenticated: false, user: null }),
  });

  render(<App />);

  expect(await screen.findByRole('region', { name: 'Login form' })).toBeDefined();
  expect(screen.queryByText('Story Mode')).toBeNull();
  expect(screen.queryByText('VS Bot')).toBeNull();
});
