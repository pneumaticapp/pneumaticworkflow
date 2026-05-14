// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';

import { FeedItemHeader } from '../FeedItemHeader';
import { KickoffOutputs } from '../../KickoffOutputs';
import { EWorkflowLogEvent, EWorkflowStatus } from '../../../types/workflow';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../types/template';
import { IHighlightsItem } from '../../../types/highlights';
import { Ellipsis } from '../Ellipsis';

jest.mock('../../KickoffOutputs', () => ({
  KickoffOutputs: jest.fn(() => null),
  EKickoffOutputsViewModes: { Short: 'short', Detailed: 'detailed' },
}));

jest.mock('../../RichText', () => ({ RichText: () => null }));
jest.mock('../../Attachments', () => ({ Attachments: () => null }));
jest.mock('../../UserData', () => ({ UserData: () => null }));
jest.mock('../Ellipsis', () => ({ Ellipsis: jest.fn(() => null) }));
jest.mock('../utils/TruncatedContent', () => ({
  TruncatedContent: ({ children }: { children: React.ReactNode }) => children,
}));

jest.mock('../../../utils/helpers', () => {
  const actual = jest.requireActual('../../../utils/helpers');
  return { isArrayWithItems: actual.isArrayWithItems };
});

jest.mock('../../../utils/users', () => ({
  getUserFullName: jest.fn(() => 'User'),
}));

jest.mock('../../../utils/dateTime', () => ({
  getSnoozedUntilDate: jest.fn(() => ''),
}));

describe('FeedItemHeader', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
    apiName: `field-${Math.random()}`,
    name: 'Field',
    type: EExtraFieldType.String,
    order: 0,
    userId: null,
    groupId: null,
    ...overrides,
  });

  const makeBaseProps = (overrides: Partial<IHighlightsItem> = {}): IHighlightsItem => ({
    id: 1,
    type: EWorkflowLogEvent.WorkflowRun,
    task: null,
    text: '',
    attachments: [],
    created: '2026-01-01T00:00:00Z',
    user: null,
    workflow: {
      id: 1,
      name: 'Test Workflow',
      currentTask: 1,
      tasksCount: 1,
      template: null,
      isLegacyTemplate: false,
      legacyTemplateName: '',
      status: EWorkflowStatus.Running,
      kickoff: null,
      isExternal: false,
    },
    userId: null,
    targetUserId: null,
    delay: null,
    ...overrides,
  });

  describe('Kickoff outputs for WorkflowRun with task=null', () => {
    it('renders KickoffOutputs with kickoff.output and fieldsets when task=null', () => {
      const kickoffFields = [
        makeField({ apiName: 'f1', order: 1, value: 'hello' }),
        makeField({ apiName: 'f2', order: 2, value: 'world' }),
      ];

      const kickoffFieldsets: IFieldsetData[] = [
        {
          id: 1,
          apiName: 'fs-1',
          name: 'Fieldset 1',
          description: '',
          order: 0,
          fields: [
            makeField({ apiName: 'fs1-f1', order: 1, value: 'fieldset value' }),
          ],
        },
      ];

      const props = makeBaseProps({
        type: EWorkflowLogEvent.WorkflowRun,
        task: null,
        workflow: {
          id: 1,
          name: 'Test Workflow',
          currentTask: 1,
          tasksCount: 1,
          template: null,
          isLegacyTemplate: false,
          legacyTemplateName: '',
          status: EWorkflowStatus.Running,
          kickoff: {
            id: 1,
            description: null,
            output: kickoffFields,
            fieldsets: kickoffFieldsets,
          },
          isExternal: false,
        },
      });

      render(React.createElement(FeedItemHeader, props));

      const mock = KickoffOutputs as jest.Mock;
      const lastCall = mock.mock.calls[mock.mock.calls.length - 1][0];
      expect(lastCall.outputs).toEqual(kickoffFields);
      expect(lastCall.fieldsets).toEqual(kickoffFieldsets);
    });
  });

  describe('Fieldsets handling in highlights', () => {
    const makeFieldset = (overrides: Partial<IFieldsetData> & { fields: IExtraField[] }): IFieldsetData => ({
      id: 1,
      apiName: 'fs-1',
      name: 'Test Fieldset',
      description: '',
      order: 0,
      ...overrides,
    });

    const makeWorkflow = (kickoff: IHighlightsItem['workflow']['kickoff']) => ({
      id: 1,
      name: 'Test Workflow',
      currentTask: 1,
      tasksCount: 1,
      template: null,
      isLegacyTemplate: false,
      legacyTemplateName: '',
      status: EWorkflowStatus.Running,
      kickoff,
      isExternal: false,
    });

    const getLastKickoffOutputsProps = () => {
      const mock = KickoffOutputs as jest.Mock;
      return mock.mock.calls[mock.mock.calls.length - 1][0];
    };

    it('passes fieldsets when outputs is empty', () => {
      const fieldsets = [
        makeFieldset({ fields: [makeField({ value: 'val1', order: 1 })] }),
      ];

      const props = makeBaseProps({
        type: EWorkflowLogEvent.WorkflowRun,
        workflow: makeWorkflow({
          id: 1,
          description: null,
          output: [],
          fieldsets,
        }),
      });

      render(React.createElement(FeedItemHeader, props));

      const mock = KickoffOutputs as jest.Mock;
      expect(mock).toHaveBeenCalled();
      expect(getLastKickoffOutputsProps().fieldsets).toEqual(fieldsets);
    });

    it.each([
      EWorkflowLogEvent.TaskComplete,
      EWorkflowLogEvent.WorkflowComplete,
      EWorkflowLogEvent.WorkflowsReturned,
    ])('uses task.fieldsets instead of kickoff.fieldsets for %s', (eventType) => {
      const kickoffFieldsets = [
        makeFieldset({ id: 10, name: 'Kickoff FS', fields: [makeField({ value: 'kickoff-val', order: 1 })] }),
      ];
      const taskFieldsets = [
        makeFieldset({ id: 20, name: 'Task FS', fields: [makeField({ value: 'task-val', order: 1 })] }),
      ];

      const props = makeBaseProps({
        type: eventType,
        task: {
          id: 1,
          name: 'Task 1',
          number: 1,
          process: 1,
          delay: null,
          output: [makeField({ value: 'task-output', order: 1 })],
          fieldsets: taskFieldsets,
          dueDate: null,
        },
        workflow: makeWorkflow({
          id: 1,
          description: null,
          output: [],
          fieldsets: kickoffFieldsets,
        }),
      });

      render(React.createElement(FeedItemHeader, props));

      const mock = KickoffOutputs as jest.Mock;
      expect(mock).toHaveBeenCalled();

      const passedFieldsets = getLastKickoffOutputsProps().fieldsets;
      expect(passedFieldsets).toEqual(taskFieldsets);
      expect(passedFieldsets).not.toEqual(kickoffFieldsets);
    });

    it('does not render KickoffOutputs for TaskRevert', () => {
      const taskFieldsets = [
        makeFieldset({ id: 20, name: 'Task FS', fields: [makeField({ value: 'task-val', order: 1 })] }),
      ];

      const props = makeBaseProps({
        type: EWorkflowLogEvent.TaskRevert,
        task: {
          id: 1,
          name: 'Task 1',
          number: 1,
          process: 1,
          delay: null,
          output: [makeField({ value: 'task-output', order: 1 })],
          fieldsets: taskFieldsets,
          dueDate: null,
        },
        workflow: makeWorkflow({
          id: 1,
          description: null,
          output: [],
          fieldsets: [],
        }),
      });

      render(React.createElement(FeedItemHeader, props));

      const mock = KickoffOutputs as jest.Mock;
      expect(mock).not.toHaveBeenCalled();
    });

    it('filters out empty fields inside fieldsets', () => {
      const fieldsets = [
        makeFieldset({
          fields: [
            makeField({ apiName: 'filled', value: 'hello', order: 1 }),
            makeField({ apiName: 'empty', value: '', order: 2 }),
          ],
        }),
      ];

      const props = makeBaseProps({
        type: EWorkflowLogEvent.WorkflowRun,
        workflow: makeWorkflow({
          id: 1,
          description: null,
          output: [],
          fieldsets,
        }),
      });

      render(React.createElement(FeedItemHeader, props));

      const mock = KickoffOutputs as jest.Mock;
      expect(mock).toHaveBeenCalled();

      const passedFieldsets = getLastKickoffOutputsProps().fieldsets;
      expect(passedFieldsets).toHaveLength(1);
      expect(passedFieldsets[0].fields).toHaveLength(1);
      expect(passedFieldsets[0].fields[0].apiName).toBe('filled');
    });

    it('removes fieldsets with all empty fields after filtering', () => {
      const fieldsets = [
        makeFieldset({
          id: 1,
          name: 'All Empty',
          fields: [
            makeField({ apiName: 'e1', value: '', order: 1 }),
            makeField({ apiName: 'e2', value: '', order: 2 }),
          ],
        }),
        makeFieldset({
          id: 2,
          name: 'Has Value',
          fields: [
            makeField({ apiName: 'f1', value: 'data', order: 1 }),
          ],
        }),
      ];

      const props = makeBaseProps({
        type: EWorkflowLogEvent.WorkflowRun,
        workflow: makeWorkflow({
          id: 1,
          description: null,
          output: [],
          fieldsets,
        }),
      });

      render(React.createElement(FeedItemHeader, props));

      const mock = KickoffOutputs as jest.Mock;
      expect(mock).toHaveBeenCalled();

      const passedFieldsets = getLastKickoffOutputsProps().fieldsets;
      expect(passedFieldsets).toHaveLength(1);
      expect(passedFieldsets[0].name).toBe('Has Value');
    });

    it('shows Ellipsis when fieldset fields count exceeds 1', () => {
      const fieldsets = [
        makeFieldset({
          fields: [
            makeField({ apiName: 'f1', value: 'v1', order: 1 }),
            makeField({ apiName: 'f2', value: 'v2', order: 2 }),
          ],
        }),
      ];

      const props = makeBaseProps({
        type: EWorkflowLogEvent.WorkflowRun,
        workflow: makeWorkflow({
          id: 1,
          description: null,
          output: [],
          fieldsets,
        }),
      });

      render(React.createElement(FeedItemHeader, props));

      expect(Ellipsis).toHaveBeenCalled();
    });
  });
});
