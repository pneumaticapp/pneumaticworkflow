import React from 'react';
import { act, render } from '@testing-library/react';

import { EExtraFieldType, IExtraField } from '../../../../types/template';
import { ITask } from '../../../../types/tasks';
import {
  addOrUpdateStorageOutput,
  fieldsetsStorage,
  getOutputFromStorage,
  removeOutputFromLocalStorage,
} from '../../utils/storageOutputs';
import { useTaskOutput } from '../useTaskOutput';

jest.mock('../../utils/storageOutputs', () => ({
  addOrUpdateStorageOutput: jest.fn(),
  getOutputFromStorage: jest.fn(),
  removeOutputFromLocalStorage: jest.fn(),
  fieldsetsStorage: { get: jest.fn(), save: jest.fn(), remove: jest.fn() },
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

const makeTask = (output: IExtraField[], overrides: Partial<ITask> = {}): ITask => ({
  id: 1,
  dateStarted: '2024-01-01',
  output,
  fieldsets: [],
  ...overrides,
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
    (fieldsetsStorage.get as jest.Mock).mockReturnValue(undefined);
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('preserves pending edits to unchanged fields when server output changes', () => {
    const initialOutput = [
      makeField('unchanged-field', 'prefilled server value'),
      makeField('changed-field', 'old server value'),
    ];
    const { rerender } = render(<HookHarness task={makeTask(initialOutput)} />);

    act(() => {
      hookResult.editField('unchanged-field')({ value: 'local value' });
    });

    rerender(
      <HookHarness
        task={makeTask([
          makeField('unchanged-field', 'prefilled server value'),
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

  it('merges stored values into the latest fieldset definition', () => {
    const storedFieldset = {
      apiNameBinding: 'fieldset-1',
      title: 'Old title',
      fields: [makeField('existing-field', 'draft value')],
    } as any;
    const newRequiredField = {
      ...makeField('new-required-field', ''),
      isRequired: true,
    };
    const serverFieldset = {
      ...storedFieldset,
      title: 'Updated title',
      fields: [
        makeField('existing-field', 'server value'),
        newRequiredField,
      ],
    };
    (fieldsetsStorage.get as jest.Mock).mockReturnValue([storedFieldset]);

    render(<HookHarness task={makeTask([], { fieldsets: [serverFieldset] })} />);

    expect(hookResult.fieldsetOutputValues).toEqual([{
      ...serverFieldset,
      fields: [
        makeField('existing-field', 'draft value'),
        newRequiredField,
      ],
    }]);
  });

  it('clears fieldset drafts and state when the same task restarts', () => {
    const serverFieldset = {
      apiNameBinding: 'fieldset-1',
      fields: [makeField('fieldset-field', 'new run value')],
    } as any;
    const staleFieldset = {
      ...serverFieldset,
      fields: [makeField('fieldset-field', 'previous run draft')],
    };
    (fieldsetsStorage.get as jest.Mock).mockReturnValue([staleFieldset]);

    const { rerender } = render(
      <HookHarness task={makeTask([], { fieldsets: [serverFieldset] })} />,
    );
    expect(hookResult.fieldsetOutputValues).toEqual([staleFieldset]);

    act(() => {
      hookResult.editFieldsetField('fieldset-field')({ value: 'pending previous run edit' });
    });
    rerender(
      <HookHarness
        task={makeTask([], {
          dateStarted: '2024-02-01',
          fieldsets: [serverFieldset],
        })}
      />,
    );

    expect(fieldsetsStorage.remove).toHaveBeenCalledWith(1);
    expect(hookResult.fieldsetOutputValues).toEqual([serverFieldset]);

    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(fieldsetsStorage.save).not.toHaveBeenCalled();
  });

  it('preserves a fieldset draft when only server presentation metadata changes', () => {
    const serverFieldset = {
      apiNameBinding: 'fieldset-1',
      title: 'Old title',
      description: 'Old description',
      order: 0,
      fields: [makeField('fieldset-field', 'server value')],
    } as any;
    const { rerender } = render(
      <HookHarness task={makeTask([], { fieldsets: [serverFieldset] })} />,
    );

    act(() => {
      hookResult.editFieldsetField('fieldset-field')({ value: 'local draft' });
    });
    rerender(
      <HookHarness
        task={makeTask([], {
          fieldsets: [{
            ...serverFieldset,
            title: 'New title',
            description: 'New description',
            order: 2,
          }],
        })}
      />,
    );

    expect(hookResult.fieldsetOutputValues).toEqual([{
      ...serverFieldset,
      title: 'New title',
      description: 'New description',
      order: 2,
      fields: [makeField('fieldset-field', 'local draft')],
    }]);
  });

  it('preserves in-memory fieldset edits when another server fieldset changes', () => {
    const unchangedFieldset = {
      apiNameBinding: 'unchanged-fieldset',
      fields: [makeField('unchanged-field', 'prefilled server value')],
    } as any;
    const changedFieldset = {
      apiNameBinding: 'changed-fieldset',
      fields: [makeField('changed-field', 'old server value')],
    } as any;
    const { rerender } = render(
      <HookHarness task={makeTask([], { fieldsets: [unchangedFieldset, changedFieldset] })} />,
    );

    act(() => {
      hookResult.editFieldsetField('unchanged-field')({ value: 'live draft' });
    });
    rerender(
      <HookHarness
        task={makeTask([], {
          fieldsets: [
            unchangedFieldset,
            {
              ...changedFieldset,
              fields: [makeField('changed-field', 'new server value')],
            },
          ],
        })}
      />,
    );

    expect(hookResult.fieldsetOutputValues).toEqual([
      {
        ...unchangedFieldset,
        fields: [makeField('unchanged-field', 'live draft')],
      },
      {
        ...changedFieldset,
        fields: [makeField('changed-field', 'new server value')],
      },
    ]);
    expect(fieldsetsStorage.save).toHaveBeenCalledWith(1, [
      {
        ...unchangedFieldset,
        fields: [makeField('unchanged-field', 'live draft')],
      },
    ]);

    act(() => {
      jest.advanceTimersByTime(300);
    });
    expect(fieldsetsStorage.save).toHaveBeenCalledTimes(1);
  });

  it('flushes a pending fieldset edit on unmount', () => {
    const fieldset = {
      apiNameBinding: 'fieldset-1',
      fields: [makeField('fieldset-field', 'server value')],
    } as any;
    const { unmount } = render(
      <HookHarness task={makeTask([], { fieldsets: [fieldset] })} />,
    );

    act(() => {
      hookResult.editFieldsetField('fieldset-field')({ value: 'last edit' });
    });
    unmount();

    expect(fieldsetsStorage.save).toHaveBeenCalledWith(1, [{
      ...fieldset,
      fields: [makeField('fieldset-field', 'last edit')],
    }]);
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

  it('does not restore flushed drafts again during unmount', () => {
    const fieldset = {
      apiNameBinding: 'fieldset-1',
      fields: [makeField('fieldset-field', 'server value')],
    } as any;
    const { unmount } = render(
      <HookHarness
        task={makeTask([makeField('field', 'server value')], { fieldsets: [fieldset] })}
      />,
    );

    act(() => {
      hookResult.editField('field')({ value: 'output draft' });
      hookResult.editFieldsetField('fieldset-field')({ value: 'fieldset draft' });
    });
    act(() => {
      hookResult.flushOutputs();
    });

    expect(addOrUpdateStorageOutput).toHaveBeenCalledTimes(1);
    expect(fieldsetsStorage.save).toHaveBeenCalledTimes(1);

    unmount();

    expect(addOrUpdateStorageOutput).toHaveBeenCalledTimes(1);
    expect(fieldsetsStorage.save).toHaveBeenCalledTimes(1);
  });

  it('flushes a pending output edit on unmount', () => {
    const initialOutput = [makeField('field', 'server value')];
    const { unmount } = render(<HookHarness task={makeTask(initialOutput)} />);

    act(() => {
      hookResult.editField('field')({ value: 'local value' });
    });
    unmount();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(addOrUpdateStorageOutput).toHaveBeenCalledTimes(1);
    expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(1, [
      makeField('field', 'local value'),
    ]);
    expect(removeOutputFromLocalStorage).not.toHaveBeenCalled();
  });
});
