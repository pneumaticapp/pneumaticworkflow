/// <reference types="jest" />
import React from 'react';
import type { FC, ReactNode } from 'react';
import { act, render } from '@testing-library/react';

import { ETaskPerformerType, ITemplateClient, ITemplateTaskClient } from '../../../../types/template';
import { TaskFormScopeProvider, TemplateFieldContext } from '../../useTemplateForm';
import { useTaskForm } from '../useTaskForm';

const makeTask = (overrides: Partial<ITemplateTaskClient> = {}): ITemplateTaskClient => ({
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
  fieldsets: overrides.fieldsets ?? [],
});

const makeTemplate = (tasks: ITemplateTaskClient[]): ITemplateClient =>
  ({
    id: 1,
    name: 'Template',
    description: '',
    isActive: false,
    finalizable: false,
    completionNotification: false,
    reminderNotification: false,
    dateUpdated: null,
    updatedBy: null,
    owners: [],
    kickoff: { description: '', fields: [] } as any,
    tasks,
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: tasks.length,
    performersCount: 0,
  }) as ITemplateClient;

interface IFormikBag {
  values: ITemplateClient;
  setFieldValue: jest.Mock;
}

function TaskFormHarness({
  bag,
  taskUuid,
  children,
}: {
  bag: IFormikBag;
  taskUuid: string;
  children: ReactNode;
}) {
  return (
    <TemplateFieldContext.Provider
      value={{ values: bag.values, setFieldValue: bag.setFieldValue, setValues: jest.fn() }}
    >
      <TaskFormScopeProvider taskUuid={taskUuid}>{children}</TaskFormScopeProvider>
    </TemplateFieldContext.Provider>
  );
}

describe('useTaskForm', () => {
  it('throws when used outside <TaskFormScopeProvider>', () => {
    const Spy: FC = () => {
      useTaskForm();
      return null;
    };

    const bag: IFormikBag = {
      values: makeTemplate([makeTask()]),
      setFieldValue: jest.fn(),
    };

    const spy = jest.spyOn(console, 'error').mockImplementation(() => undefined);

    expect(() =>
      render(
        <TemplateFieldContext.Provider
          value={{ values: bag.values, setFieldValue: bag.setFieldValue, setValues: jest.fn() }}
        >
          <Spy />
        </TemplateFieldContext.Provider>,
      ),
    ).toThrow(/TaskFormScopeProvider/);

    spy.mockRestore();
  });

  it('binds updateField to tasks[index].<field> via setFieldValue', () => {
    const setFieldValue = jest.fn();
    const task = makeTask({ uuid: 'uuid-1', name: 'Old' });
    const bag: IFormikBag = { values: makeTemplate([task]), setFieldValue };

    let form: ReturnType<typeof useTaskForm> | null = null;
    const Spy: FC = () => {
      form = useTaskForm();
      return null;
    };

    render(
      <TaskFormHarness bag={bag} taskUuid="uuid-1">
        <Spy />
      </TaskFormHarness>,
    );

    act(() => {
      form!.updateField('name')('New name');
    });

    expect(setFieldValue).toHaveBeenCalledWith('tasks.0.name', 'New name', false);
  });

  it('binds updateTask to tasks[index] via setFieldValue, merging onto the current task', () => {
    const setFieldValue = jest.fn();
    const task = makeTask({ uuid: 'uuid-1', description: 'old', rawPerformers: [] });
    const bag: IFormikBag = { values: makeTemplate([task]), setFieldValue };

    let form: ReturnType<typeof useTaskForm> | null = null;
    const Spy: FC = () => {
      form = useTaskForm();
      return null;
    };

    render(
      <TaskFormHarness bag={bag} taskUuid="uuid-1">
        <Spy />
      </TaskFormHarness>,
    );

    const newPerformers = [
      {
        apiName: 'performer-1',
        type: ETaskPerformerType.User,
        label: 'User 1',
        sourceId: '1',
      },
    ];

    act(() => {
      form!.updateTask({ rawPerformers: newPerformers, requireCompletionByAll: true });
    });

    expect(setFieldValue).toHaveBeenCalledTimes(1);
    expect(setFieldValue).toHaveBeenCalledWith(
      'tasks.0',
      { ...task, rawPerformers: newPerformers, requireCompletionByAll: true },
      false,
    );
  });

  it('targets the correct index when the scoped task is not the first one', () => {
    const setFieldValue = jest.fn();
    const task1 = makeTask({ uuid: 'uuid-1', name: 'First' });
    const task2 = makeTask({ uuid: 'uuid-2', name: 'Second', number: 2 });
    const bag: IFormikBag = { values: makeTemplate([task1, task2]), setFieldValue };

    let form: ReturnType<typeof useTaskForm> | null = null;
    const Spy: FC = () => {
      form = useTaskForm();
      return null;
    };

    render(
      <TaskFormHarness bag={bag} taskUuid="uuid-2">
        <Spy />
      </TaskFormHarness>,
    );

    expect(form!.task).toEqual(task2);

    act(() => {
      form!.updateField('name')('Updated second');
    });

    expect(setFieldValue).toHaveBeenCalledWith('tasks.1.name', 'Updated second', false);
  });
});
