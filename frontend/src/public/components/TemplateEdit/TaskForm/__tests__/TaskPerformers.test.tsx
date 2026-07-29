import * as React from 'react';
import { render } from '@testing-library/react';

import { intlMock } from '../../../../__stubs__/intlMock';
import { makeTemplateTaskClient } from '../../../../__stubs__/templates.factory';
import { Checkbox } from '../../../UI/Fields/Checkbox';
import { ITemplateTaskClient } from '../../../../types/template';
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
  createDueDateApiName: jest.fn(() => 'due-date-mock'),
}));

describe('TaskPerformers', () => {
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const SKIP_LABEL = formatMsg('templates.task-skip-for-starter');

  const mockSetCurrentTask = jest.fn();

  const makeTask = (overrides: Partial<ITemplateTaskClient> = {}) =>
    makeTemplateTaskClient({
      name: 'Test Task',
      ...overrides,
    });

  const renderComponent = (taskOverrides: Partial<ITemplateTaskClient> = {}) => {
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

  type TCheckboxProps = Record<string, unknown>;

  const findCheckboxProps = (checkboxId: string): TCheckboxProps => {
    const calls = (Checkbox as jest.Mock).mock.calls;
    const match = calls.find((c: [TCheckboxProps, Record<string, never>]) => c[0].checkboxId === checkboxId);
    if (!match) throw new Error(`Checkbox call with checkboxId="${checkboxId}" not found`);
    return match[0];
  };

  const renderTwoTasks = () => {
    const task1 = makeTask({ apiName: 'task-1' });
    const task2 = makeTask({ apiName: 'task-2' });
    const setCurrentTask1 = jest.fn();
    const setCurrentTask2 = jest.fn();

    render(
      React.createElement(
        'div',
        null,
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
      const completeByAllCall = calls.find((c: [TCheckboxProps, Record<string, never>]) =>
        (c[0].checkboxId as string)?.startsWith('completeByAll-'),
      );
      const skipForStarterCall = calls.find((c: [TCheckboxProps, Record<string, never>]) =>
        (c[0].checkboxId as string)?.startsWith('skipForStarter-'),
      );

      if (!completeByAllCall) throw new Error('completeByAll checkbox call not found');
      if (!skipForStarterCall) throw new Error('skipForStarter checkbox call not found');

      expect(completeByAllCall[0].checkboxId).toBe('completeByAll-custom-task-123');
      expect(skipForStarterCall[0].checkboxId).toBe('skipForStarter-custom-task-123');
    });

    it('two tasks produce different checkboxIds (no DOM id collisions)', () => {
      renderTwoTasks();

      const calls = (Checkbox as jest.Mock).mock.calls;
      const checkboxIds = calls.map((c: [TCheckboxProps, Record<string, never>]) => c[0].checkboxId as string);

      const completeByAllIds = checkboxIds.filter((id) => id?.startsWith('completeByAll-'));
      const skipForStarterIds = checkboxIds.filter((id) => id?.startsWith('skipForStarter-'));

      expect(completeByAllIds).toEqual(['completeByAll-task-1', 'completeByAll-task-2']);
      expect(skipForStarterIds).toEqual(['skipForStarter-task-1', 'skipForStarter-task-2']);
    });

    it('uses checkboxId prop (not id) to ensure proper label-input binding', () => {
      renderComponent();

      const calls = (Checkbox as jest.Mock).mock.calls;

      calls.forEach((c: [TCheckboxProps, Record<string, never>]) => {
        expect(c[0].checkboxId).toBeDefined();
        expect(c[0].id).toBeUndefined();
      });
    });
  });

  describe('requireCompletionByAll checkbox', () => {
    it('passes title with correct localization text', () => {
      renderComponent();

      const props = findCheckboxProps('completeByAll-task-1');

      expect(props.title).toBe(formatMsg('templates.task-require-completion-by-all'));
    });

    it('passes checked=true when requireCompletionByAll=true', () => {
      renderComponent({ requireCompletionByAll: true });

      const props = findCheckboxProps('completeByAll-task-1');

      expect(props.checked).toBe(true);
    });

    it('passes checked=false when requireCompletionByAll=false', () => {
      renderComponent({ requireCompletionByAll: false });

      const props = findCheckboxProps('completeByAll-task-1');

      expect(props.checked).toBe(false);
    });

    it('calls setCurrentTask with requireCompletionByAll on onChange', () => {
      renderComponent({ requireCompletionByAll: false });

      const props = findCheckboxProps('completeByAll-task-1');
      const onChangeFn = props.onChange as (e: { currentTarget: { checked: boolean } }) => void;
      onChangeFn({ currentTarget: { checked: true } });

      expect(mockSetCurrentTask).toHaveBeenCalledWith({ requireCompletionByAll: true });
    });
  });

  describe('skipForStarter checkbox', () => {
    it('passes title with correct localization text', () => {
      renderComponent();

      const props = findCheckboxProps('skipForStarter-task-1');

      expect(props.title).toBe(SKIP_LABEL);
    });

    it('passes checked=true when skipForStarter=true', () => {
      renderComponent({ skipForStarter: true });

      const props = findCheckboxProps('skipForStarter-task-1');

      expect(props.checked).toBe(true);
    });

    it('passes checked=false when skipForStarter=false', () => {
      renderComponent({ skipForStarter: false });

      const props = findCheckboxProps('skipForStarter-task-1');

      expect(props.checked).toBe(false);
    });

    it('calls setCurrentTask with true on onChange', () => {
      renderComponent({ skipForStarter: false });

      const props = findCheckboxProps('skipForStarter-task-1');
      const onChangeFn = props.onChange as (e: { currentTarget: { checked: boolean } }) => void;
      onChangeFn({ currentTarget: { checked: true } });

      expect(mockSetCurrentTask).toHaveBeenCalledWith({ skipForStarter: true });
    });

    it('calls setCurrentTask with false on checkbox uncheck', () => {
      renderComponent({ skipForStarter: true });

      const props = findCheckboxProps('skipForStarter-task-1');
      const onChangeFn = props.onChange as (e: { currentTarget: { checked: boolean } }) => void;
      onChangeFn({ currentTarget: { checked: false } });

      expect(mockSetCurrentTask).toHaveBeenCalledWith({ skipForStarter: false });
    });
  });
});
