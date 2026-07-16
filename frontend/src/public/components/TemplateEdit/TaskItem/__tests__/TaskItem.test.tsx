import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ITemplateTaskClient } from '../../../../types/template';
import { makeFieldsetBindingClient } from '../../../../__stubs__/fieldsets.factory';
import { makeTemplateTaskClient } from '../../../../__stubs__/templates.factory';
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

jest.mock('../../TaskForm/utils/getTaskVariables', () => ({
  getVariables: jest.fn(() => []),
}));

jest.mock('../../FieldsetOutputsPreview/FieldsetOutputsPreview', () => ({
  FieldsetOutputsPreview: (props: {
    fieldsets: Array<{ apiNameBinding: string }>;
    onGroupClick?: () => void;
  }) =>
    React.createElement(
      'div',
      null,
      props.fieldsets.map((fieldset) =>
        React.createElement(
          'button',
          {
            key: fieldset.apiNameBinding,
            type: 'button',
            onClick: props.onGroupClick,
          },
          fieldset.apiNameBinding,
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

describe('TaskItem', () => {
  const makeTask = (overrides: Partial<ITemplateTaskClient> = {}) => makeTemplateTaskClient({
    name: 'Task 1',
    fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1' })],
    ...overrides,
  });

  beforeEach(() => {
    jest.clearAllMocks();
    (getKickoff as jest.Mock).mockReturnValue({ fields: [], fieldsets: [] });
    (getTemplateTasks as jest.Mock).mockReturnValue([]);
    (getTemplateData as jest.Mock).mockReturnValue({ id: 1 });
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
