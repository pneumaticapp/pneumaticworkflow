/// <reference types="jest" />
import * as React from 'react';
import { act, render } from '@testing-library/react';
import { FormikProvider, useFormik } from 'formik';

import { ITemplateTask } from '../../../../types/template';
import { TaskFormPersistProvider, useTaskForm } from '../useTaskForm';

const makeTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask => ({
  apiName: 'task-1',
  number: 1,
  name: 'Test Task',
  description: '',
  delay: null,
  rawDueDate: null as any,
  requireCompletionByAll: false,
  skipForStarter: false,
  rawPerformers: [],
  fields: [],
  uuid: 'uuid-1',
  conditions: [],
  checklists: [],
  revertTask: null,
  ancestors: [],
  ...overrides,
});

const flushPersist = () => act(async () => {
  await new Promise((resolve) => setTimeout(resolve, 0));
});

interface IHarnessProps {
  task: ITemplateTask;
  patchTask: jest.Mock;
  children: React.ReactNode;
}

function TaskFormHarness({ task, patchTask, children }: IHarnessProps) {
  const formik = useFormik<ITemplateTask>({
    initialValues: task,
    enableReinitialize: true,
    onSubmit: () => undefined,
  });

  return (
    <FormikProvider value={formik}>
      <TaskFormPersistProvider patchTask={patchTask} task={task}>
        {children}
      </TaskFormPersistProvider>
    </FormikProvider>
  );
}

describe('TaskFormPersistProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not patch when the external task prop changes', async () => {
    const patchTask = jest.fn();
    const task1 = makeTask({ uuid: 'uuid-1', name: 'Task 1' });
    const task2 = makeTask({ uuid: 'uuid-2', name: 'Task 2' });

    const { rerender } = render(
      <TaskFormHarness task={task1} patchTask={patchTask}>
        <span />
      </TaskFormHarness>,
    );

    await flushPersist();
    patchTask.mockClear();

    rerender(
      <TaskFormHarness task={task2} patchTask={patchTask}>
        <span />
      </TaskFormHarness>,
    );

    await flushPersist();

    expect(patchTask).not.toHaveBeenCalled();
  });

  it('batches rapid field updates into a single patch', async () => {
    const patchTask = jest.fn();
    const task = makeTask({ description: 'old', checklists: [] });

    function DescriptionEditorSimulator() {
      const { updateField } = useTaskForm();

      return (
        <button
          type="button"
          onClick={() => {
            updateField('checklists')([{
              apiName: 'checklist-1',
              selections: [{ apiName: 'item-1', value: 'Item' }],
            }]);
            updateField('description')('new description');
          }}
        >
          edit
        </button>
      );
    }

    const { getByRole } = render(
      <TaskFormHarness task={task} patchTask={patchTask}>
        <DescriptionEditorSimulator />
      </TaskFormHarness>,
    );

    await flushPersist();
    patchTask.mockClear();

    act(() => {
      getByRole('button', { name: 'edit' }).click();
    });
    await flushPersist();

    expect(patchTask).toHaveBeenCalledTimes(1);
    expect(patchTask).toHaveBeenCalledWith({
      taskUUID: 'uuid-1',
      changedFields: {
        checklists: [{
          apiName: 'checklist-1',
          selections: [{ apiName: 'item-1', value: 'Item' }],
        }],
        description: 'new description',
      },
    });
  });
});
