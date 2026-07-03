/// <reference types="jest" />
import * as React from 'react';
import { act, render } from '@testing-library/react';
import { FormikProvider, useFormik } from 'formik';

import { intlMock } from '../../../../__stubs__/intlMock';
import { Checkbox } from '../../../UI/Fields/Checkbox';
import { ITemplate, ITemplateTask } from '../../../../types/template';
import { TaskPerformers } from '../TaskPerformers';
import { TaskFormScopeProvider, TemplateFieldContext } from '../../useTemplateForm';

jest.mock('../../../UI/Fields/Checkbox', () => ({
  Checkbox: jest.fn(() => null),
}));

jest.mock('../../../UI/form/UsersDropdown', () => ({
  UsersDropdown: jest.fn(() => null),
}));

jest.mock('../../../UI/UserPerformer', () => ({
  UserPerformer: jest.fn(() => null),
  EBgColorTypes: { Light: 'light' },
}));

jest.mock('../utils/getPerformersForDropdown', () => ({
  getPerformersForDropdown: jest.fn(() => []),
}));

jest.mock('../../../../utils/analytics', () => ({
  trackInviteTeamInPage: jest.fn(),
}));

jest.mock('../../../../utils/users', () => ({
  getUserFullName: jest.fn(),
}));

jest.mock('../../../../utils/createId', () => ({
  createPerformerApiName: jest.fn(() => 'perf-mock'),
}));

describe('TaskPerformers', () => {
  const t = (id: string) => intlMock.formatMessage({ id });
  const SKIP_LABEL = t('templates.task-skip-for-starter');

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

  const makeTemplate = (tasks: ITemplateTask[]): ITemplate =>
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
    }) as ITemplate;

  const flushPersist = () => act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });

  const createTaskFormWrapper = (task: ITemplateTask, setFieldValue = jest.fn()) => {
    function TaskFormTestWrapper({ children }: { children: React.ReactNode }) {
      const formik = useFormik<ITemplate>({
        initialValues: makeTemplate([task]),
        enableReinitialize: true,
        onSubmit: () => undefined,
      });

      return (
        <FormikProvider value={formik}>
          <TemplateFieldContext.Provider
            value={{ values: formik.values, setFieldValue, setValues: jest.fn() }}
          >
            <TaskFormScopeProvider taskUuid={task.uuid}>{children}</TaskFormScopeProvider>
          </TemplateFieldContext.Provider>
        </FormikProvider>
      );
    }

    return TaskFormTestWrapper;
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('checkbox identifiers', () => {
    it('generates unique checkboxId using task.apiName to prevent HTML id collisions', () => {
      const task = makeTask({ apiName: 'custom-task-123' });
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const completeByAllCall = calls.find((c: any[]) => c[0].checkboxId?.startsWith('completeByAll-'));
      const skipForStarterCall = calls.find((c: any[]) => c[0].checkboxId?.startsWith('skipForStarter-'));

      expect(completeByAllCall).toBeDefined();
      expect(skipForStarterCall).toBeDefined();

      expect(completeByAllCall![0].checkboxId).toBe('completeByAll-custom-task-123');
      expect(skipForStarterCall![0].checkboxId).toBe('skipForStarter-custom-task-123');
    });

    it('uses checkboxId prop (not id) to ensure proper label-input binding', () => {
      const task = makeTask();
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;

      calls.forEach((c: any[]) => {
        expect(c[0].checkboxId).toBeDefined();
        expect(c[0].id).toBeUndefined();
      });
    });
  });

  describe('requireCompletionByAll checkbox', () => {
    it('passes title with correct localization text', () => {
      const task = makeTask();
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const call = calls.find((c: any[]) => c[0].checkboxId === 'completeByAll-task-1');

      expect(call).toBeDefined();
      expect(call![0].title).toBe(t('templates.task-require-completion-by-all'));
    });

    it('passes checked=true when requireCompletionByAll=true', () => {
      const task = makeTask({ requireCompletionByAll: true });
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const call = calls.find((c: any[]) => c[0].checkboxId === 'completeByAll-task-1');

      expect(call![0].checked).toBe(true);
    });

    it('passes checked=false when requireCompletionByAll=false', () => {
      const task = makeTask({ requireCompletionByAll: false });
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const call = calls.find((c: any[]) => c[0].checkboxId === 'completeByAll-task-1');

      expect(call![0].checked).toBe(false);
    });

    it('calls setFieldValue with tasks.0.requireCompletionByAll on onChange', async () => {
      const task = makeTask({ requireCompletionByAll: false });
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const call = calls.find((c: any[]) => c[0].checkboxId === 'completeByAll-task-1');
      const onChangeFn = call![0].onChange;

      act(() => {
        onChangeFn({ currentTarget: { checked: true } });
      });
      await flushPersist();

      expect(setFieldValue).toHaveBeenCalledWith('tasks.0', { ...task, requireCompletionByAll: true }, false);
    });
  });

  describe('skipForStarter checkbox', () => {
    it('passes title with correct localization text', () => {
      const task = makeTask();
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const skipCall = calls.find((c: any[]) => c[0].checkboxId === 'skipForStarter-task-1');

      expect(skipCall).toBeDefined();
      expect(skipCall![0].title).toBe(SKIP_LABEL);
    });

    it('passes checked=true when skipForStarter=true', () => {
      const task = makeTask({ skipForStarter: true });
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const skipCall = calls.find((c: any[]) => c[0].checkboxId === 'skipForStarter-task-1');

      expect(skipCall![0].checked).toBe(true);
    });

    it('passes checked=false when skipForStarter=false', () => {
      const task = makeTask({ skipForStarter: false });
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const skipCall = calls.find((c: any[]) => c[0].checkboxId === 'skipForStarter-task-1');

      expect(skipCall![0].checked).toBe(false);
    });

    it('calls setFieldValue with true on onChange', async () => {
      const task = makeTask({ skipForStarter: false });
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const skipCall = calls.find((c: any[]) => c[0].checkboxId === 'skipForStarter-task-1');
      const onChangeFn = skipCall![0].onChange;

      act(() => {
        onChangeFn({ currentTarget: { checked: true } });
      });
      await flushPersist();

      expect(setFieldValue).toHaveBeenCalledWith('tasks.0', { ...task, skipForStarter: true }, false);
    });

    it('calls setFieldValue with false on checkbox uncheck', async () => {
      const task = makeTask({ skipForStarter: true });
      const setFieldValue = jest.fn();
      const Wrapper = createTaskFormWrapper(task, setFieldValue);

      render(
        React.createElement(
          Wrapper,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      );

      const calls = (Checkbox as jest.Mock).mock.calls;
      const skipCall = calls.find((c: any[]) => c[0].checkboxId === 'skipForStarter-task-1');
      const onChangeFn = skipCall![0].onChange;

      act(() => {
        onChangeFn({ currentTarget: { checked: false } });
      });
      await flushPersist();

      expect(setFieldValue).toHaveBeenCalledWith('tasks.0', { ...task, skipForStarter: false }, false);
    });
  });
});
