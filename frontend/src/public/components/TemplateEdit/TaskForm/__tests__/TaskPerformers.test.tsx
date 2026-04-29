/// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';

import { intlMock } from '../../../../__stubs__/intlMock';
import { Checkbox } from '../../../UI/Fields/Checkbox';
import { ITemplateTask } from '../../../../types/template';

// TaskPerformers использует `import React from 'react'` (default import),
// который не работает с ts-jest без esModuleInterop.
// Мокаем модуль react, чтобы default === module
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

// Отложенный импорт после мока react
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
    uuid: 'uuid-1',
    conditions: [],
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  });

  const renderComponent = (taskOverrides: Partial<ITemplateTask> = {}) => {
    return render(
      React.createElement(TaskPerformers, {
        task: makeTask(taskOverrides),
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
      (c: any[]) => c[0].checkboxId === 'skipForStarter',
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Чекбокс skipForStarter', () => {
    it('передаёт title с правильным текстом локализации', () => {
      renderComponent();

      const skipCall = getSkipCheckboxCall();

      expect(skipCall).toBeDefined();
      expect(skipCall![0].title).toBe(SKIP_LABEL);
    });

    it('передаёт checked=true при skipForStarter=true', () => {
      renderComponent({ skipForStarter: true });

      const skipCall = getSkipCheckboxCall();

      expect(skipCall![0].checked).toBe(true);
    });

    it('передаёт checked=false при skipForStarter=false', () => {
      renderComponent({ skipForStarter: false });

      const skipCall = getSkipCheckboxCall();

      expect(skipCall![0].checked).toBe(false);
    });

    it('вызывает setCurrentTask с true при onChange', () => {
      renderComponent({ skipForStarter: false });

      const skipCall = getSkipCheckboxCall();
      const onChangeFn = skipCall![0].onChange;
      onChangeFn({ currentTarget: { checked: true } });

      expect(mockSetCurrentTask).toHaveBeenCalledWith(
        { skipForStarter: true },
      );
    });

    it('вызывает setCurrentTask с false при снятии чекбокса', () => {
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
