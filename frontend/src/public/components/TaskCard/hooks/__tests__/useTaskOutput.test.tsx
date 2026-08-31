import React from 'react';
import { render } from '@testing-library/react';

import { makeFieldsetRuntime } from '../../../../__stubs__/fieldsets.factory';
import { makeTask } from '../../../../__stubs__/tasks.factory';
import { ITask } from '../../../../types/tasks';
import { EExtraFieldType, IExtraField } from '../../../../types/template';
import { fieldsetsStorage } from '../../utils/storageOutputs';
import { useTaskOutput } from '../useTaskOutput';

jest.mock('../../utils/storageOutputs', () => ({
  addOrUpdateStorageOutput: jest.fn(),
  getOutputFromStorage: jest.fn(),
  fieldsetsStorage: { get: jest.fn(), save: jest.fn() },
}));

const makeField = (apiName: string, value: string, isRequired = false): IExtraField => ({
  apiName,
  name: apiName,
  type: EExtraFieldType.String,
  order: 0,
  value,
  isRequired,
  userId: null,
  groupId: null,
});

let hookResult: ReturnType<typeof useTaskOutput>;

const HookHarness = ({ task }: { task: ITask }) => {
  hookResult = useTaskOutput(task);
  return null;
};

describe('useTaskOutput', () => {
  it('merges stored field values into the latest server fieldset definition', () => {
    const storedFieldset = makeFieldsetRuntime({
      fields: [makeField('existing-field', 'draft value')],
    });
    const serverFieldset = makeFieldsetRuntime({
      title: 'Updated fieldset',
      fields: [
        makeField('existing-field', 'server value'),
        makeField('new-required-field', '', true),
      ],
    });
    (fieldsetsStorage.get as jest.Mock).mockReturnValue([storedFieldset]);

    render(
      <HookHarness
        task={makeTask({ fieldsets: [serverFieldset] })}
      />,
    );

    expect(hookResult.fieldsetOutputValues).toEqual([{
      ...serverFieldset,
      fields: [
        makeField('existing-field', 'draft value'),
        makeField('new-required-field', '', true),
      ],
    }]);
  });
});
