import { act, fireEvent, render, screen } from '@testing-library/react';
import { IonApp } from '@ionic/react';
import { afterEach, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import PracticeTopics from './PracticeTopics';
import PracticeTopScore from './PracticeTopScore';
import VsBot from './VsBot';
import { appRoutes } from '../routing/routes';

const renderFlow = () =>
  render(
    <IonApp>
      <MemoryRouter initialEntries={[appRoutes.practice]}>
        <Routes>
          <Route path={appRoutes.practice} element={<VsBot />} />
          <Route path={appRoutes.practiceTopScore} element={<PracticeTopScore />} />
          <Route path={appRoutes.practiceTopics} element={<PracticeTopics />} />
        </Routes>
      </MemoryRouter>
    </IonApp>,
  );

afterEach(() => {
  vi.useRealTimers();
});

test('opens the topic catalogue on its own route and selects a topic', () => {
  vi.useFakeTimers();
  renderFlow();

  expect(screen.getByRole('heading', { name: 'How will you challenge the archive?' })).toBeDefined();
  expect(screen.queryByRole('heading', { name: 'Select a topic' })).toBeNull();

  fireEvent.click(screen.getByRole('button', { name: /choose by topic/i }));
  act(() => vi.advanceTimersByTime(360));

  expect(screen.getByRole('heading', { name: 'Select a topic' })).toBeDefined();

  const ancientCivilizations = screen.getByRole('button', {
    name: /ancient civilizations/i,
  });
  fireEvent.click(ancientCivilizations);

  expect(ancientCivilizations.getAttribute('aria-pressed')).toBe('true');
  expect(screen.getByText('Ancient Civilizations selected. Your training path is ready.')).toBeDefined();
});

test('opens the blank top-score page on its own route', () => {
  vi.useFakeTimers();
  renderFlow();

  fireEvent.click(screen.getByRole('button', { name: /top score/i }));
  act(() => vi.advanceTimersByTime(360));

  expect(screen.getByRole('heading', { name: 'Top Score' })).toBeDefined();
  expect(screen.queryByRole('button', { name: /top score/i })).toBeNull();
});
