import { render, screen, act } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { OfflineQueueProvider, useOfflineQueue } from '@/lib/OfflineQueueContext';
import { api } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  api: {
    syncBatch: vi.fn()
  }
}));

function TestComponent() {
  const { enqueue, isOffline } = useOfflineQueue();
  
  return (
    <div>
      <span data-testid="status">{isOffline ? 'offline' : 'online'}</span>
      <button onClick={() => enqueue({ method: 'POST', path: '/test', body: {} })}>
        Enqueue
      </button>
    </div>
  );
}

test('OfflineQueueProvider handles enqueue and syncs online', async () => {
  render(
    <OfflineQueueProvider>
      <TestComponent />
    </OfflineQueueProvider>
  );

  // Default is online in jsdom
  expect(screen.getByTestId('status').textContent).toBe('online');

  // Enqueue should call syncBatch immediately since online
  await act(async () => {
    screen.getByText('Enqueue').click();
  });
  
  // Wait for promise resolution
  await new Promise(r => setTimeout(r, 10));

  expect(api.syncBatch).toHaveBeenCalled();
});

test('splitSyncResults keeps nothing sent twice and separates refused reports', async () => {
  const { splitSyncResults } = await import('@/lib/OfflineQueueContext');
  const ops = ['a', 'b', 'c', 'd'].map((op_id) => ({ op_id, method: 'POST', path: '/cases', body: {} }));
  const { done, failed } = splitSyncResults(ops, [
    { op_id: 'a', status: 'applied' },
    { op_id: 'b', status: 'error' },
    { op_id: 'c', status: 'duplicate' },
  ]);
  expect(done).toEqual(['a', 'c']);
  expect(failed).toEqual(['b']);
  // 'd' got no answer: it must stay on the phone and be sent again later
  expect([...done, ...failed]).not.toContain('d');
});
