import React from 'react';
import { act, render } from '@testing-library/react';

import { EExtraFieldType, IExtraField } from '../../../../types/template';
import { ITask } from '../../../../types/tasks';
import {
  addOrUpdateStorageOutput,
  getOutputFromStorage,
  removeOutputFromLocalStorage,
} from '../../utils/storageOutputs';
import { useTaskOutput } from '../useTaskOutput';

jest.mock('../../utils/storageOutputs', () => ({
  addOrUpdateStorageOutput: jest.fn(),
  getOutputFromStorage: jest.fn(),
  removeOutputFromLocalStorage: jest.fn(),
}));

const makeField = (apiName: string, value: string): IExtraField => ({
  apiName,
  name: apiName,
  type: EExtraFieldType.String,
  order: 0,
  value,
  userId: null,
  groupId: null,
});

const makeTask = (output: IExtraField[]): ITask => ({
  id: 1,
  dateStarted: '2024-01-01',
  output,
} as ITask);

let hookResult: ReturnType<typeof useTaskOutput>;

const HookHarness = ({ task }: { task: ITask }) => {
  hookResult = useTaskOutput(task);

  return null;
};

describe('useTaskOutput', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    (getOutputFromStorage as jest.Mock).mockReturnValue(undefined);
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('preserves pending edits to unchanged fields when server output changes', () => {
    const initialOutput = [
      makeField('unchanged-field', ''),
      makeField('changed-field', 'old server value'),
    ];
    const { rerender } = render(<HookHarness task={makeTask(initialOutput)} />);

    act(() => {
      hookResult.editField('unchanged-field')({ value: 'local value' });
    });

    rerender(
      <HookHarness
        task={makeTask([
          makeField('unchanged-field', ''),
          makeField('changed-field', 'new server value'),
        ])}
      />,
    );

    expect(hookResult.outputValues).toEqual([
      makeField('unchanged-field', 'local value'),
      makeField('changed-field', 'new server value'),
    ]);
    expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(1, [
      makeField('unchanged-field', 'local value'),
    ]);

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(addOrUpdateStorageOutput).toHaveBeenCalledTimes(1);
  });

  it('persists an edit after the debounce delay', () => {
    const initialOutput = [makeField('field', 'server value')];
    render(<HookHarness task={makeTask(initialOutput)} />);

    act(() => {
      hookResult.editField('field')({ value: 'local value' });
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(1, [
      makeField('field', 'local value'),
    ]);
  });

  it('cancels a pending storage write on unmount', () => {
    const initialOutput = [makeField('field', 'server value')];
    const { unmount } = render(<HookHarness task={makeTask(initialOutput)} />);

    act(() => {
      hookResult.editField('field')({ value: 'local value' });
    });
    unmount();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(addOrUpdateStorageOutput).not.toHaveBeenCalled();
    expect(removeOutputFromLocalStorage).not.toHaveBeenCalled();
  });
});
