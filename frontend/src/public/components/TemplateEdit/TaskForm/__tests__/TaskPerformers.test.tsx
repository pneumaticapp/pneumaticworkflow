import * as React from 'react';
import { render } from '@testing-library/react';

import { intlMock } from '../../../../__stubs__/intlMock';
import { Checkbox } from '../../../UI/Fields/Checkbox';
import { ITemplateTask } from '../../../../types/template';

// TaskPerformers uses `import React from 'react'` (default import),
// which doesn't work with ts-jest without esModuleInterop.
// Mocking the react module so that default === module
jest.mock('react', () => {
  const actual = jest.requireActual('react');
  return { ...actual, default: actual, __esModule: true };
});

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

// Deferred import after react mock
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { TaskPerformers } = require('../TaskPerformers');

describe('TaskPerformers', () => {
  const t = (id: string) => intlMock.formatMessage({ id });
  const SKIP_LABEL = t('templates.task-skip-for-starter');

  const mockSetCurrentTask = jest.fn();

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
    fieldsets: [],
    uuid: 'uuid-1',
    conditions: [],
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  });

  const renderComponent = (taskOverrides: Partial<ITemplateTask> = {}) => {
    const task = makeTask(taskOverrides);
    return render(
      React.createElement(TaskPerformers, {
        task,
        tasks: [task],
        users: [],
        variables: [],
        isTeamInvitesModalOpen: false,
        setCurrentTask: mockSetCurrentTask,
      }),
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
    const setCurrentTask1 = jest.fn();
    const setCurrentTask2 = jest.fn();

    render(
      React.createElement('div', null,
        React.createElement(TaskPerformers, {
          task: task1,
          tasks: [task1, task2],
          users: [],
          variables: [],
          isTeamInvitesModalOpen: false,
          setCurrentTask: setCurrentTask1,
        }),
        React.createElement(TaskPerformers, {
          task: task2,
          tasks: [task1, task2],
          users: [],
          variables: [],
          isTeamInvitesModalOpen: false,
          setCurrentTask: setCurrentTask2,
        }),
      ),
    );

    return { setCurrentTask1, setCurrentTask2 };
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

      expect(completeByAllIds).toEqual(['completeByAll-task-1', 'completeByAll-task-2']);
      expect(skipForStarterIds).toEqual(['skipForStarter-task-1', 'skipForStarter-task-2']);
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

    it('calls setCurrentTask with requireCompletionByAll on onChange', () => {
      renderComponent({ requireCompletionByAll: false });

      const call = getCompleteByAllCall();
      const onChangeFn = call![0].onChange;
      onChangeFn({ currentTarget: { checked: true } });

      expect(mockSetCurrentTask).toHaveBeenCalledWith(
        { requireCompletionByAll: true },
      );
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

    it('calls setCurrentTask with true on onChange', () => {
      renderComponent({ skipForStarter: false });

      const skipCall = getSkipCheckboxCall();
      const onChangeFn = skipCall![0].onChange;
      onChangeFn({ currentTarget: { checked: true } });

      expect(mockSetCurrentTask).toHaveBeenCalledWith(
        { skipForStarter: true },
      );
    });

    it('calls setCurrentTask with false on checkbox uncheck', () => {
      renderComponent({ skipForStarter: true });

      const skipCall = getSkipCheckboxCall();
      const onChangeFn = skipCall![0].onChange;
      onChangeFn({ currentTarget: { checked: false } });

      expect(mockSetCurrentTask).toHaveBeenCalledWith(
        { skipForStarter: false },
      );
    });
  });
});
