import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';
import App from './App';

beforeEach(() => {
  vi.spyOn(window.HTMLMediaElement.prototype, 'play').mockResolvedValue();
  vi.spyOn(window.HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
});

afterEach(() => {
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
