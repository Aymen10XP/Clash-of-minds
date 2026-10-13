import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import TestIonRouter from '../../test/TestIonRouter';
import { startTopScore } from '../../features/quiz/api';
import Practice from './Practice';
import PracticeTopScore from './top-score/PracticeTopScore';
import PracticeTopics from './topics/PracticeTopics';
import { appRoutes } from '../../routing/routes';

vi.mock('../../features/quiz/api', async () => {
  const actual = await vi.importActual<typeof import('../../features/quiz/api')>(
    '../../features/quiz/api',
  );
  return { ...actual, startTopScore: vi.fn() };
});

const renderFlow = () =>
  render(
    <TestIonRouter initialEntry={appRoutes.practice}>
      <Routes>
        <Route path={appRoutes.practice} element={<Practice />} />
        <Route path={appRoutes.practiceTopScore} element={<PracticeTopScore />} />
        <Route path={appRoutes.practiceTopScoreTopic} element={<PracticeTopScore />} />
        <Route path={appRoutes.practiceTopics} element={<PracticeTopics />} />
      </Routes>
    </TestIonRouter>,
  );

beforeEach(() => {
  vi.mocked(startTopScore).mockImplementation(() => new Promise(() => undefined));
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

test('starts a top-score run with the selected topic', () => {
  vi.useFakeTimers();
  renderFlow();

  expect(screen.getByRole('group', { name: 'VS Bot modes' })).toBeDefined();
  expect(screen.getByRole('button', { name: /choose by topic/i })).toBeDefined();
  expect(screen.queryByRole('heading', { name: 'Select a topic' })).toBeNull();

  fireEvent.click(screen.getByRole('button', { name: /choose by topic/i }));
  act(() => vi.advanceTimersByTime(360));

  expect(screen.getByRole('heading', { name: 'Select a topic' })).toBeDefined();

  const ancientCivilizations = screen.getByRole('button', {
    name: /ancient civilizations/i,
  });
  fireEvent.click(ancientCivilizations);

  expect(screen.getByRole('heading', { name: 'Top Score' })).toBeDefined();
  expect(startTopScore).toHaveBeenCalledWith('ancient-civilizations');
});

test('starts an unrestricted top-score run from the main practice mode', () => {
  vi.useFakeTimers();
  renderFlow();

  fireEvent.click(screen.getByRole('button', { name: /top score/i }));
  act(() => vi.advanceTimersByTime(360));

  expect(screen.getByRole('heading', { name: 'Top Score' })).toBeDefined();
  expect(screen.queryByRole('button', { name: /top score/i })).toBeNull();
  expect(startTopScore).toHaveBeenCalledWith(undefined);
});
