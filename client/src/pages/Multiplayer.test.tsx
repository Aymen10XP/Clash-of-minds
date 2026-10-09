import { act, fireEvent, render, screen } from '@testing-library/react';
import { IonApp } from '@ionic/react';
import { afterEach, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import FriendlyMatch from './FriendlyMatch';
import Multiplayer from './Multiplayer';
import RankedMatchmaking from './RankedMatchmaking';
import { appRoutes } from '../routing/routes';

const renderFlow = () =>
  render(
    <IonApp>
      <MemoryRouter initialEntries={[appRoutes.multiplayer]}>
        <Routes>
          <Route path={appRoutes.multiplayer} element={<Multiplayer />} />
          <Route path={appRoutes.multiplayerRanked} element={<RankedMatchmaking />} />
          <Route path={appRoutes.multiplayerFriendly} element={<FriendlyMatch />} />
        </Routes>
      </MemoryRouter>
    </IonApp>,
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

test('opens the friendly match placeholder', () => {
  vi.useFakeTimers();
  renderFlow();

  fireEvent.click(screen.getByRole('button', { name: /friendly match/i }));
  act(() => vi.advanceTimersByTime(360));

  expect(screen.getByRole('heading', { name: 'Friendly Match' })).toBeDefined();
  expect(screen.queryByRole('button', { name: /friendly match/i })).toBeNull();
});
