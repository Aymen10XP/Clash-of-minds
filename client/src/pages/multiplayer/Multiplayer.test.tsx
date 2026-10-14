import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import TestIonRouter from '../../test/TestIonRouter';
import Multiplayer from './Multiplayer';
import FriendlyMatch from './friendly/FriendlyMatch';
import RankedMatchmaking from './ranked/RankedMatchmaking';
import { appRoutes } from '../../routing/routes';

vi.mock('../../features/multiplayer/api', () => ({
  fetchInvitations: vi.fn(() => new Promise(() => undefined)),
  fetchMatches: vi.fn(() => new Promise(() => undefined)),
  searchMultiplayerPlayers: vi.fn(),
  sendMatchInvitation: vi.fn(),
  respondToMatchInvitation: vi.fn(),
  cancelMatchInvitation: vi.fn(),
}));

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

test('opens the friendly match lobby foundation', () => {
  vi.useFakeTimers();
  renderFlow();

  fireEvent.click(screen.getByRole('button', { name: /friendly match/i }));
  act(() => vi.advanceTimersByTime(360));

  expect(screen.getByRole('heading', { name: 'Friendly Match' })).toBeDefined();
  expect(screen.getByRole('heading', { name: 'Find a player' })).toBeDefined();
  expect(screen.getByRole('heading', { name: 'Invitations' })).toBeDefined();
  expect(screen.getByRole('heading', { name: 'Battle rooms' })).toBeDefined();
  expect(screen.queryByRole('button', { name: /friendly match/i })).toBeNull();
});
