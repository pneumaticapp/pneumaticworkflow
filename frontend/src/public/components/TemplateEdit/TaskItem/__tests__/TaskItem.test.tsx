import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ITemplateTask, IFieldsetData } from '../../../../types/template';
import { makeFieldsetData } from '../../../../__stubs__/fieldsets.factory';
import { ETaskFormParts } from '../../types';

jest.mock('react', () => {
  const actual = jest.requireActual('react');
  return { ...actual, default: actual, __esModule: true };
});

jest.mock('../../../../redux/selectors/template', () => ({
  getKickoff: jest.fn(),
  getTemplateTasks: jest.fn(),
  getTemplateData: jest.fn(),
}));

jest.mock('../../../../redux/selectors/fieldsets', () => ({
  getFieldsetsCatalogByApiName: jest.fn(),
}));

jest.mock('../../TaskForm/utils/getTaskVariables', () => ({
  getVariables: jest.fn(() => []),
}));

jest.mock('../../FieldsetOutputsPreview/FieldsetOutputsPreview', () => ({
  FieldsetOutputsPreview: (props: {
    fieldsets: Array<{ apiName: string }>;
    onGroupClick?: () => void;
  }) =>
    React.createElement(
      'div',
      null,
      props.fieldsets.map((fs) =>
        React.createElement(
          'button',
          {
            key: fs.apiName,
            type: 'button',
            onClick: props.onGroupClick,
          },
          fs.apiName,
        ),
      ),
    ),
}));

jest.mock('../../ExtraFields/utils/ExtraFieldsLabels', () => ({
  ExtraFieldsLabels: () => null,
}));
jest.mock('../TaskItemUsers', () => ({
  TaskItemUsers: () => null,
}));
jest.mock('../../../RichText', () => ({
  RichText: () => null,
}));
jest.mock('../../TaskRenderDueInInfo', () => ({
  TaskRenderDueIn: jest.fn(() => null),
}));
jest.mock('../../TaskRenderConditionsInfo', () => ({
  TaskRenderConditionsInfo: jest.fn(() => null),
}));
jest.mock('../../TaskRenderReturnInfo', () => ({
  TaskRenderReturnInfo: jest.fn(() => null),
}));

import { TaskItem } from '../TaskItem';
import {
  getKickoff,
  getTemplateTasks,
  getTemplateData,
} from '../../../../redux/selectors/template';
import { getFieldsetsCatalogByApiName } from '../../../../redux/selectors/fieldsets';

describe('TaskItem', () => {
  const makeTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask => ({
    id: 1,
    apiName: 'task-1',
    name: 'Task 1',
    description: '',
    number: 1,
    rawPerformers: [],
    requireCompletionByAll: false,
    skipForStarter: false,
    fields: [],
    fieldsets: [{ apiName: 'fs-1', order: 0 }],
    delay: null,
    rawDueDate: null as any,
    conditions: [],
    uuid: 'uuid-1',
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  });

  const fieldsetData = makeFieldsetData({ id: 100, name: 'My Fieldset' });

  beforeEach(() => {
    jest.clearAllMocks();
    (getKickoff as jest.Mock).mockReturnValue({ fields: [], fieldsets: [] });
    (getTemplateTasks as jest.Mock).mockReturnValue([]);
    (getTemplateData as jest.Mock).mockReturnValue({ id: 1 });
    (getFieldsetsCatalogByApiName as jest.Mock).mockReturnValue(
      new Map<string, IFieldsetData>([['fs-1', fieldsetData]]),
    );
  });

  describe('click on fieldset preview', () => {
    it('sets scrollTarget to Fields (not Fieldsets) and opens the task form', () => {
      const setScrollTarget = jest.fn();
      const toggleIsOpenTask = jest.fn();

      render(
        React.createElement(TaskItem, {
          task: makeTask(),
          setScrollTarget,
          toggleIsOpenTask,
        }),
      );

      userEvent.click(screen.getByRole('button', { name: 'fs-1' }));

      expect(setScrollTarget).toHaveBeenCalledTimes(1);
      expect(setScrollTarget).toHaveBeenCalledWith(ETaskFormParts.Fields);
      expect(toggleIsOpenTask).toHaveBeenCalledTimes(1);
    });
  });
});
