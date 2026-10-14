import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import {
  closeMatchRoom,
  fetchMatch,
  MultiplayerApiError,
  requestMatchRematch,
  submitMatchAnswer,
  type KnowledgeMatch,
} from '../../../features/multiplayer/api';
import TestIonRouter from '../../../test/TestIonRouter';
import MatchRoom from './MatchRoom';

vi.mock('../../../features/multiplayer/api', async () => {
  const actual = await vi.importActual<typeof import('../../../features/multiplayer/api')>(
    '../../../features/multiplayer/api',
  );
  return {
    ...actual,
    fetchMatch: vi.fn(),
    closeMatchRoom: vi.fn(),
    markMatchReady: vi.fn(),
    requestMatchRematch: vi.fn(),
    submitMatchAnswer: vi.fn(),
  };
});

const activeMatch: KnowledgeMatch = {
  id: 'match-1',
  status: 'active',
  createdAt: '2026-10-14T12:00:00Z',
  startedAt: '2026-10-14T12:00:00Z',
  endedAt: null,
  endReason: null,
  winnerId: null,
  durationMs: 300_000,
  remainingMs: 295_000,
  participants: [
    { id: 1, username: 'alice', country: 'TN', seat: 'host', score: 0, hearts: 3, ready: true, closed: false, rematchRequested: false, isCurrentUser: true },
    { id: 2, username: 'bob', country: 'US', seat: 'guest', score: 0, hearts: 3, ready: true, closed: false, rematchRequested: false, isCurrentUser: false },
  ],
  currentRound: {
    sequence: 1,
    durationMs: 15_000,
    remainingMs: 14_500,
    hasAnswered: false,
    selectedChoiceId: null,
    question: {
      id: 7,
      topic: { slug: 'history', title: 'History' },
      prompt: 'Which city was the capital?',
      difficulty: 'easy',
      choices: [
        { id: 70, text: 'Carthage' },
        { id: 71, text: 'Rome' },
        { id: 72, text: 'Athens' },
        { id: 73, text: 'Sparta' },
      ],
    },
  },
  lastRound: null,
  rematchMatchId: null,
};

const renderRoom = () => render(
  <TestIonRouter initialEntry="/multiplayer/match/match-1">
    <Routes>
      <Route path="/multiplayer/match/:matchId" element={<MatchRoom />} />
      <Route path="/multiplayer/friendly" element={<div>Friendly lobby</div>} />
    </Routes>
  </TestIonRouter>,
);

beforeEach(() => {
  vi.mocked(fetchMatch).mockResolvedValue(activeMatch);
  vi.mocked(submitMatchAnswer).mockResolvedValue({
    ...activeMatch,
    currentRound: { ...activeMatch.currentRound!, hasAnswered: true, selectedChoiceId: 70 },
  });
  vi.mocked(requestMatchRematch).mockResolvedValue(activeMatch);
  vi.mocked(closeMatchRoom).mockResolvedValue({ terminated: false, match: activeMatch });
});

afterEach(() => {
  vi.clearAllMocks();
});

test('renders the synchronized duel and submits an answer', async () => {
  renderRoom();

  expect(await screen.findByRole('heading', { name: 'Which city was the capital?' })).toBeDefined();
  expect(screen.getAllByRole('button', { name: /carthage|rome|athens|sparta/i })).toHaveLength(4);

  fireEvent.click(screen.getByRole('button', { name: /carthage/i }));

  await waitFor(() => expect(submitMatchAnswer).toHaveBeenCalledWith('match-1', 7, 70));
  expect(await screen.findByText(/answer locked/i)).toBeDefined();
});

test('returns to the friendly lobby when the room has been terminated', async () => {
  vi.mocked(fetchMatch).mockRejectedValueOnce(new MultiplayerApiError('Room not found.', 404));
  renderRoom();

  expect(await screen.findByText('Friendly lobby')).toBeDefined();
});
