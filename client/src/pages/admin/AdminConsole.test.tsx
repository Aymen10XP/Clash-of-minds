import { fireEvent, render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';
import TestIonRouter from '../../test/TestIonRouter';
import { appRoutes } from '../../routing/routes';
import AdminConsole from './AdminConsole';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  fetchMock.mockResolvedValue({
    ok: true,
    json: async () => ({
      users: [],
      indicators: { activeUsers: 0, activeTopics: 0, activeQuestions: 0, matchesByStatus: {} },
      auditEvents: [],
    }),
  });
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test('keeps the admin console mounted while editing every answer', async () => {
  const { container } = render(
    <TestIonRouter initialEntry={appRoutes.admin}>
      <AdminConsole />
    </TestIonRouter>,
  );

  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/api/auth/admin/users/', expect.anything()));
  const answerInputs = Array.from(
    container.querySelectorAll<HTMLInputElement>('.admin-answer input:not([type="radio"])'),
  );
  expect(answerInputs).toHaveLength(4);
  expect(container.textContent).toContain('Project dashboard');
  expect(container.querySelector('.admin-indicators')).not.toBeNull();

  ['Mercury', 'Venus', 'Earth', 'Mars'].forEach((answer, index) => {
    fireEvent.change(answerInputs[index], { target: { value: answer } });
  });

  expect(answerInputs.map((input) => input.value)).toEqual(['Mercury', 'Venus', 'Earth', 'Mars']);
  expect(container.querySelector('.admin-page')).not.toBeNull();
});
