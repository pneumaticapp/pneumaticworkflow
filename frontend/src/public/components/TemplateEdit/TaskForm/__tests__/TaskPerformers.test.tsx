/// <reference types="jest" />
import * as React from 'react';
import { act, render } from '@testing-library/react';
import { FormikProvider, useFormik } from 'formik';

import { intlMock } from '../../../../__stubs__/intlMock';
import { Checkbox } from '../../../UI/Fields/Checkbox';
import { ITemplateTask } from '../../../../types/template';
import { TaskPerformers } from '../TaskPerformers';

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

  const mockPatchTask = jest.fn();

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

  const createTaskFormWrapper = (task: ITemplateTask, patchTask = mockPatchTask) => {
    function TaskFormTestWrapper({ children }: { children: React.ReactNode }) {
      const formik = useFormik<ITemplateTask>({
        initialValues: task,
        enableReinitialize: true,
        onSubmit: () => undefined,
      });

      return React.createElement(
        FormikProvider,
        { value: formik },
        React.createElement(
          TaskFormPersistProvider,
          { patchTask, task, children },
        ),
      );
    }

    return TaskFormTestWrapper;
  };

  const renderComponent = (taskOverrides: Partial<ITemplateTask> = {}) => {
    const task = makeTask(taskOverrides);
    const Wrapper = createTaskFormWrapper(task);

    return render(
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
  };

  const getSkipCheckboxCall = () => {
    const calls = (Checkbox as jest.Mock).mock.calls;
    return calls.find(
      (c: any[]) => c[0].checkboxId === 'skipForStarter-task-1',
    );
  };

  const getCompleteByAllCall = () => {
    const calls = (Checkbox as jest.Mock).mock.calls;
    return calls.find(
      (c: any[]) => c[0].checkboxId === 'completeByAll-task-1',
    );
  };

  const renderTwoTasks = () => {
    const task1 = makeTask({ apiName: 'task-1' });
    const task2 = makeTask({ apiName: 'task-2' });
    const mockPatchTask1 = jest.fn();
    const mockPatchTask2 = jest.fn();
    const Wrapper1 = createTaskFormWrapper(task1, mockPatchTask1);
    const Wrapper2 = createTaskFormWrapper(task2, mockPatchTask2);

    render(
      React.createElement('div', null,
        React.createElement(
          Wrapper1,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task1, task2],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
        React.createElement(
          Wrapper2,
          null,
          React.createElement(TaskPerformers, {
            tasks: [task1, task2],
            users: [],
            variables: [],
            isTeamInvitesModalOpen: false,
          }),
        ),
      ),
    );

    return { mockPatchTask1, mockPatchTask2 };
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('checkbox identifiers', () => {
    it('generates unique checkboxId using task.apiName to prevent HTML id collisions', () => {
      renderComponent({ apiName: 'custom-task-123' });

      const calls = (Checkbox as jest.Mock).mock.calls;
      const completeByAllCall = calls.find((c: any[]) => c[0].checkboxId?.startsWith('completeByAll-'));
      const skipForStarterCall = calls.find((c: any[]) => c[0].checkboxId?.startsWith('skipForStarter-'));

      expect(completeByAllCall).toBeDefined();
      expect(skipForStarterCall).toBeDefined();

      expect(completeByAllCall![0].checkboxId).toBe('completeByAll-custom-task-123');
      expect(skipForStarterCall![0].checkboxId).toBe('skipForStarter-custom-task-123');
    });

    it('two tasks produce different checkboxIds (no DOM id collisions)', () => {
      renderTwoTasks();

      const calls = (Checkbox as jest.Mock).mock.calls;
      const checkboxIds = calls.map((c: any[]) => c[0].checkboxId);

      const completeByAllIds = checkboxIds.filter((id: string) => id?.startsWith('completeByAll-'));
      const skipForStarterIds = checkboxIds.filter((id: string) => id?.startsWith('skipForStarter-'));

      expect([...new Set(completeByAllIds)]).toEqual(['completeByAll-task-1', 'completeByAll-task-2']);
      expect([...new Set(skipForStarterIds)]).toEqual(['skipForStarter-task-1', 'skipForStarter-task-2']);
    });

    it('uses checkboxId prop (not id) to ensure proper label-input binding', () => {
      renderComponent();

      const calls = (Checkbox as jest.Mock).mock.calls;

      calls.forEach((c: any[]) => {
        expect(c[0].checkboxId).toBeDefined();
        expect(c[0].id).toBeUndefined();
      });
    });
  });

  describe('requireCompletionByAll checkbox', () => {
    it('passes title with correct localization text', () => {
      renderComponent();

      const call = getCompleteByAllCall();

      expect(call).toBeDefined();
      expect(call![0].title).toBe(t('templates.task-require-completion-by-all'));
    });

    it('passes checked=true when requireCompletionByAll=true', () => {
      renderComponent({ requireCompletionByAll: true });

      const call = getCompleteByAllCall();

      expect(call![0].checked).toBe(true);
    });

    it('passes checked=false when requireCompletionByAll=false', () => {
      renderComponent({ requireCompletionByAll: false });

      const call = getCompleteByAllCall();

      expect(call![0].checked).toBe(false);
    });

    it('calls patchTask with requireCompletionByAll on onChange', () => {
      renderComponent({ requireCompletionByAll: false });

      const call = getCompleteByAllCall();
      const onChangeFn = call![0].onChange;
      act(() => {
        onChangeFn({ currentTarget: { checked: true } });
      });

      expect(mockPatchTask).toHaveBeenCalledWith({
        taskUUID: 'uuid-1',
        changedFields: { requireCompletionByAll: true },
      });
    });
  });

  describe('skipForStarter checkbox', () => {
    it('passes title with correct localization text', () => {
      renderComponent();

      const skipCall = getSkipCheckboxCall();

      expect(skipCall).toBeDefined();
      expect(skipCall![0].title).toBe(SKIP_LABEL);
    });

    it('passes checked=true when skipForStarter=true', () => {
      renderComponent({ skipForStarter: true });

      const skipCall = getSkipCheckboxCall();

      expect(skipCall![0].checked).toBe(true);
    });

    it('passes checked=false when skipForStarter=false', () => {
      renderComponent({ skipForStarter: false });

      const skipCall = getSkipCheckboxCall();

      expect(skipCall![0].checked).toBe(false);
    });

    it('calls patchTask with true on onChange', () => {
      renderComponent({ skipForStarter: false });

      const skipCall = getSkipCheckboxCall();
      const onChangeFn = skipCall![0].onChange;
      act(() => {
        onChangeFn({ currentTarget: { checked: true } });
      });

      expect(mockPatchTask).toHaveBeenCalledWith({
        taskUUID: 'uuid-1',
        changedFields: { skipForStarter: true },
      });
    });

    it('calls patchTask with false on checkbox uncheck', () => {
      renderComponent({ skipForStarter: true });

      const skipCall = getSkipCheckboxCall();
      const onChangeFn = skipCall![0].onChange;
      act(() => {
        onChangeFn({ currentTarget: { checked: false } });
      });

      expect(mockPatchTask).toHaveBeenCalledWith({
        taskUUID: 'uuid-1',
        changedFields: { skipForStarter: false },
      });
    });
  });
});
