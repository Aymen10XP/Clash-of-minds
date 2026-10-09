import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import TestIonRouter from '../../test/TestIonRouter';
import Multiplayer from './Multiplayer';
import FriendlyMatch from './friendly/FriendlyMatch';
import RankedMatchmaking from './ranked/RankedMatchmaking';
import { appRoutes } from '../../routing/routes';

const renderFlow = () =>
  render(
    <TestIonRouter initialEntry={appRoutes.multiplayer}>
      <Routes>
        <Route path={appRoutes.multiplayer} element={<Multiplayer />} />
        <Route path={appRoutes.multiplayerRanked} element={<RankedMatchmaking />} />
        <Route path={appRoutes.multiplayerFriendly} element={<FriendlyMatch />} />
      </Routes>
    </TestIonRouter>,
  );

afterEach(() => {
  vi.useRealTimers();
});

test('opens the ranked matchmaking placeholder', () => {
  vi.useFakeTimers();
  renderFlow();

  fireEvent.click(screen.getByRole('button', { name: /ranked matchmaking/i }));
  act(() => vi.advanceTimersByTime(360));

  expect(screen.getByRole('heading', { name: 'Ranked Matchmaking' })).toBeDefined();
  expect(screen.queryByRole('button', { name: /ranked matchmaking/i })).toBeNull();
});

test('returns from a multiplayer destination with backward navigation', () => {
  vi.useFakeTimers();
  renderFlow();

  fireEvent.click(screen.getByRole('button', { name: /ranked matchmaking/i }));
  act(() => vi.advanceTimersByTime(220));
  fireEvent.click(screen.getByLabelText('Go back'));
  act(() => vi.advanceTimersByTime(140));

  expect(screen.getByRole('heading', { name: 'Multiplayer' })).toBeDefined();
  expect(screen.getByRole('button', { name: /ranked matchmaking/i })).toBeDefined();
});

test('opens the friendly match placeholder', () => {
  vi.useFakeTimers();
  renderFlow();

  fireEvent.click(screen.getByRole('button', { name: /friendly match/i }));
  act(() => vi.advanceTimersByTime(360));

  expect(screen.getByRole('heading', { name: 'Friendly Match' })).toBeDefined();
  expect(screen.queryByRole('button', { name: /friendly match/i })).toBeNull();
});
