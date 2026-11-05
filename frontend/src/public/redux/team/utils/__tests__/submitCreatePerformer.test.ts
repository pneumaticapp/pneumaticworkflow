import { runSaga, stdChannel } from 'redux-saga';
import { call } from 'redux-saga/effects';

import { submitCreatePerformer } from '../submitCreatePerformer';
import { closeCreatePerformerModal, createPerformerFailed, createPerformerStarted } from '../../slice';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn() },
  checkSomeRouteIsActive: jest.fn(() => false),
}));

describe('submitCreatePerformer', () => {
  const dispatched: unknown[] = [];

  const start = (request: () => Promise<unknown>) => {
    const channel = stdChannel();
    const task = runSaga(
      {
        channel,
        dispatch: (action) => {
          dispatched.push(action);
        },
        getState: () => ({}),
      },
      function* runSubmit() {
        yield call(submitCreatePerformer, call(request));
      },
    );

    return { channel, task };
  };

  beforeEach(() => {
    dispatched.length = 0;
  });

  it('closes the modal after a successful request', async () => {
    await start(() => Promise.resolve()).task.toPromise();

    expect(dispatched).toEqual([createPerformerStarted(), closeCreatePerformerModal()]);
  });

  it('keeps the modal open and rethrows when the request fails', async () => {
    const error = new Error('Invalid');

    await expect(start(() => Promise.reject(error)).task.toPromise()).rejects.toBe(error);
    expect(dispatched).toEqual([createPerformerStarted(), createPerformerFailed()]);
  });

  it('does not touch a modal that was closed during the request', async () => {
    let resolveRequest: () => void = () => undefined;
    const { channel, task } = start(
      () =>
        new Promise<void>((resolve) => {
          resolveRequest = resolve;
        }),
    );

    channel.put(closeCreatePerformerModal());
    resolveRequest();
    await task.toPromise();

    expect(dispatched).toEqual([createPerformerStarted()]);
  });
});
