import React from 'react';
import { act, render } from '@testing-library/react';

import { EExtraFieldType, IExtraField } from '../../../../types/template';
import { ITask } from '../../../../types/tasks';
import {
  addOrUpdateStorageOutput,
  fieldsetsStorage,
  getOutputFromStorage,
  outputStorage,
  removeOutputFromLocalStorage,
} from '../../utils/storageOutputs';
import { getTaskOutputFingerprint } from '../../utils/getTaskOutputFingerprint';
import { useTaskOutput } from '../useTaskOutput';

jest.mock('../../utils/storageOutputs', () => ({
  addOrUpdateStorageOutput: jest.fn(),
  getOutputFromStorage: jest.fn(),
  removeOutputFromLocalStorage: jest.fn(),
  outputStorage: { getEntry: jest.fn() },
  fieldsetsStorage: {
    get: jest.fn(),
    getEntry: jest.fn(),
    save: jest.fn(),
    remove: jest.fn(),
  },
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
let renderedFieldsetValues: ReturnType<typeof useTaskOutput>['fieldsetOutputValues'][] = [];

const HookHarness = ({ task }: { task: ITask }) => {
  hookResult = useTaskOutput(task);
  renderedFieldsetValues.push(hookResult.fieldsetOutputValues);

  return null;
};

describe('useTaskOutput', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    renderedFieldsetValues = [];
    (getOutputFromStorage as jest.Mock).mockReturnValue(undefined);
    (outputStorage.getEntry as jest.Mock).mockReturnValue(undefined);
    (fieldsetsStorage.getEntry as jest.Mock).mockReturnValue(undefined);
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('exposes server fieldsets on the first render', () => {
    const fieldset = {
      apiNameBinding: 'fieldset-1',
      fields: [makeField('fieldset-field', 'server value')],
    } as any;

    render(<HookHarness task={makeTask([], { fieldsets: [fieldset] })} />);

    expect(renderedFieldsetValues[0]).toEqual([fieldset]);
  });

  it('filters stale output and fieldset drafts on initial mount', () => {
    const unchangedOutput = makeField('unchanged-output', 'server value');
    const changedOutput = makeField('changed-output', 'new server value');
    const oldChangedOutput = makeField('changed-output', 'old server value');
    const unchangedField = makeField('unchanged-field', 'server value');
    const changedField = makeField('changed-field', 'new server value');
    const oldChangedField = makeField('changed-field', 'old server value');
    const storedFieldset = {
      apiNameBinding: 'fieldset-1',
      fields: [
        { ...unchangedField, value: 'valid local draft' },
        { ...oldChangedField, value: 'stale local draft' },
      ],
    } as any;
    (outputStorage.getEntry as jest.Mock).mockReturnValue({
      taskId: 1,
      data: [
        { ...unchangedOutput, value: 'valid local draft' },
        { ...oldChangedOutput, value: 'stale local draft' },
      ],
      metadata: {
        dateStarted: '2024-01-01',
        fieldFingerprints: {
          'unchanged-output': getTaskOutputFingerprint([unchangedOutput]),
          'changed-output': getTaskOutputFingerprint([oldChangedOutput]),
        },
      },
    });
    (fieldsetsStorage.getEntry as jest.Mock).mockReturnValue({
      taskId: 1,
      data: [storedFieldset],
      metadata: {
        dateStarted: '2024-01-01',
        fieldFingerprints: {
          'fieldset-1': {
            'unchanged-field': getTaskOutputFingerprint([unchangedField]),
            'changed-field': getTaskOutputFingerprint([oldChangedField]),
          },
        },
      },
    });

    render(
      <HookHarness
        task={makeTask([unchangedOutput, changedOutput], {
          fieldsets: [{
            ...storedFieldset,
            fields: [unchangedField, changedField],
          }],
        })}
      />,
    );

    expect(hookResult.outputValues).toEqual([
      { ...unchangedOutput, value: 'valid local draft' },
      changedOutput,
    ]);
    expect(hookResult.fieldsetOutputValues[0].fields).toEqual([
      { ...unchangedField, value: 'valid local draft' },
      changedField,
    ]);
  });

  it('restores legacy drafts without rewriting them with current fingerprints', () => {
    const outputField = makeField('output-field', 'server value');
    const fieldsetField = makeField('fieldset-field', 'server value');
    const serverFieldset = {
      apiNameBinding: 'fieldset-1',
      fields: [fieldsetField],
    } as any;
    (outputStorage.getEntry as jest.Mock).mockReturnValue({
      taskId: 1,
      data: [{ ...outputField, value: 'legacy output draft' }],
    });
    (fieldsetsStorage.getEntry as jest.Mock).mockReturnValue({
      taskId: 1,
      data: [{
        ...serverFieldset,
        fields: [{ ...fieldsetField, value: 'legacy fieldset draft' }],
      }],
    });

    render(
      <HookHarness
        task={makeTask([outputField], { fieldsets: [serverFieldset] })}
      />,
    );

    expect(hookResult.outputValues).toEqual([
      { ...outputField, value: 'legacy output draft' },
    ]);
    expect(hookResult.fieldsetOutputValues[0].fields).toEqual([
      { ...fieldsetField, value: 'legacy fieldset draft' },
    ]);
    expect(addOrUpdateStorageOutput).not.toHaveBeenCalled();
    expect(fieldsetsStorage.save).not.toHaveBeenCalled();
  });

  it('updates output metadata without discarding valid drafts', () => {
    const firstField = { ...makeField('first-field', 'server value'), order: 0 };
    const secondField = { ...makeField('second-field', 'second value'), order: 1 };
    const { rerender } = render(
      <HookHarness task={makeTask([firstField, secondField])} />,
    );

    act(() => {
      hookResult.editField('first-field')({ value: 'local draft' });
    });
    rerender(
      <HookHarness
        task={makeTask([
          {
            ...firstField,
            name: 'Updated name',
            order: 2,
            isHidden: true,
            isRequired: true,
          },
          secondField,
        ])}
      />,
    );

    expect(hookResult.outputValues).toEqual([
      {
        ...firstField,
        name: 'Updated name',
        order: 2,
        isHidden: true,
        isRequired: true,
        value: 'local draft',
      },
      secondField,
    ]);
  });

  it('cancels pending output persistence when the task restarts', () => {
    const field = makeField('field', 'server value');
    const { rerender } = render(<HookHarness task={makeTask([field])} />);

    act(() => {
      hookResult.editField('field')({ value: 'old run draft' });
    });
    rerender(
      <HookHarness
        task={makeTask([field], { dateStarted: '2024-02-01' })}
      />,
    );
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(removeOutputFromLocalStorage).toHaveBeenCalledWith(1);
    expect(addOrUpdateStorageOutput).not.toHaveBeenCalled();
    expect(hookResult.outputValues).toEqual([field]);
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
    expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(
      1,
      [makeField('unchanged-field', 'local value')],
      expect.any(Object),
    );

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
    (fieldsetsStorage.getEntry as jest.Mock).mockReturnValue({ taskId: 1, data: [storedFieldset] });

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
    (fieldsetsStorage.getEntry as jest.Mock).mockReturnValue({ taskId: 1, data: [staleFieldset] });

    const { rerender } = render(
      <HookHarness task={makeTask([], { fieldsets: [serverFieldset] })} />,
    );
    expect(hookResult.fieldsetOutputValues).toEqual([staleFieldset]);
    jest.clearAllMocks();

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

  it('preserves sibling field drafts when another field in the same fieldset changes', () => {
    const serverFieldset = {
      apiNameBinding: 'fieldset-1',
      fields: [
        makeField('unchanged-field', 'unchanged server value'),
        makeField('changed-field', 'old server value'),
      ],
    } as any;
    const { rerender } = render(
      <HookHarness task={makeTask([], { fieldsets: [serverFieldset] })} />,
    );

    act(() => {
      hookResult.editFieldsetField('unchanged-field')({ value: 'local draft' });
    });
    rerender(
      <HookHarness
        task={makeTask([], {
          fieldsets: [{
            ...serverFieldset,
            fields: [
              makeField('unchanged-field', 'unchanged server value'),
              makeField('changed-field', 'new server value'),
            ],
          }],
        })}
      />,
    );

    expect(hookResult.fieldsetOutputValues).toEqual([{
      ...serverFieldset,
      fields: [
        makeField('unchanged-field', 'local draft'),
        makeField('changed-field', 'new server value'),
      ],
    }]);
    expect(fieldsetsStorage.save).toHaveBeenCalledWith(
      1,
      [{
        ...serverFieldset,
        fields: [makeField('unchanged-field', 'local draft')],
      }],
      expect.any(Object),
    );
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
    expect(fieldsetsStorage.save).toHaveBeenCalledWith(
      1,
      [{
        ...unchangedFieldset,
        fields: [makeField('unchanged-field', 'live draft')],
      }],
      expect.any(Object),
    );

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

    expect(fieldsetsStorage.save).toHaveBeenCalledWith(
      1,
      [{
        ...fieldset,
        fields: [makeField('fieldset-field', 'last edit')],
      }],
      expect.any(Object),
    );
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

    expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(
      1,
      [makeField('field', 'local value')],
      expect.any(Object),
    );
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
    expect(addOrUpdateStorageOutput).toHaveBeenCalledWith(
      1,
      [makeField('field', 'local value')],
      expect.any(Object),
    );
    expect(removeOutputFromLocalStorage).not.toHaveBeenCalled();
  });
});
