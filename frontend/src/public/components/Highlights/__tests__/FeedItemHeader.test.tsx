import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useSelector } from 'react-redux';
import userEvent from '@testing-library/user-event';

import { FeedItemHeader } from '../FeedItemHeader';
import { KickoffOutputs } from '../../KickoffOutputs';
import { EWorkflowLogEvent, EWorkflowStatus } from '../../../types/workflow';
import { EExtraFieldType, IExtraField } from '../../../types/template';
import { IFieldsetRuntime } from '../../../types/fieldset';
import { makeExtraField } from '../../../__stubs__/fields.factory';
import { makeFieldsetRuntime } from '../../../__stubs__/fieldsets.factory';
import { makeHighlightsItem } from '../../../__stubs__/highlights.factory';
import { IHighlightsItem } from '../../../types/highlights';
import { Ellipsis } from '../Ellipsis';
import { intlMock } from '../../../__stubs__/intlMock';

jest.mock('react-redux', () => ({
  useSelector: jest.fn(),
}));

jest.mock('../../KickoffOutputs', () => ({
  KickoffOutputs: jest.fn(() => null),
  EKickoffOutputsViewModes: { Short: 'short', Detailed: 'detailed' },
}));

jest.mock('../../RichText', () => ({ RichText: () => null }));
jest.mock('../../Attachments', () => ({ Attachments: () => null }));
jest.mock('../../UserData', () => ({ UserData: () => null }));
jest.mock('../../UserDataWithGroup', () => ({
  __esModule: true,
  default: ({
    children,
  }: {
    children: (group: { firstName: string }) => React.ReactNode;
  }) => children({ firstName: 'Engineering Team' }),
}));
jest.mock('../Ellipsis', () => ({
  Ellipsis: jest.fn(({ expand }: { expand: () => void }) => (
    <button type="button" data-testid="ellipsis" onClick={expand}>
      ellipsis
    </button>
  )),
}));
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

const GROUP_NAME = 'Engineering Team';

const mockState = {
  authUser: { isSuperuser: false, account: {} },
  groups: {
    list: [{ id: 5, name: GROUP_NAME }],
  },
  accounts: { isCreateUserModalOpen: false },
};

describe('FeedItemHeader', () => {
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const ADDED_GROUP_LABEL = formatMsg('task.log-added-performer-group');
  const REMOVED_GROUP_LABEL = formatMsg('task.log-removed-performer-group');

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((selector) => selector(mockState));
  });

  const makeField = (overrides: Partial<IExtraField> = {}) =>
    makeExtraField({
      apiName: `field-${Math.random()}`,
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
    targetGroupId: null,
    delay: null,
    ...overrides,
  });

  describe('Kickoff outputs for WorkflowRun with task=null', () => {
    it('renders KickoffOutputs with kickoff.output and fieldsets when task=null', () => {
      const kickoffFields = [
        makeField({ apiName: 'f1', order: 1, value: 'hello' }),
        makeField({ apiName: 'f2', order: 2, value: 'world' }),
      ];

      const kickoffFieldsets: IFieldsetRuntime[] = [
        makeFieldsetRuntime({
          fields: [makeField({ apiName: 'fs1-f1', order: 1, value: 'fieldset value' })],
        }),
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
    const makeFieldset = (overrides: Partial<IFieldsetRuntime> & { fields: IExtraField[] }) =>
      makeFieldsetRuntime({
        name: 'Test Fieldset',
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
      const fieldsets = [makeFieldset({ fields: [makeField({ value: 'val1', order: 1 })] })];

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

    it.each([EWorkflowLogEvent.TaskComplete, EWorkflowLogEvent.WorkflowComplete, EWorkflowLogEvent.WorkflowsReturned])(
      'uses task.fieldsets instead of kickoff.fieldsets for %s',
      (eventType) => {
        const kickoffFieldsets = [
          makeFieldset({
            apiNameBinding: 'fs-kickoff',
            name: 'Kickoff FS',
            fields: [makeField({ value: 'kickoff-val', order: 1 })],
          }),
        ];
        const taskFieldsets = [
          makeFieldset({
            apiNameBinding: 'fs-task',
            name: 'Task FS',
            fields: [makeField({ value: 'task-val', order: 1 })],
          }),
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
      },
    );

    it('does not render KickoffOutputs for TaskRevert', () => {
      const taskFieldsets = [
        makeFieldset({
          apiNameBinding: 'fs-task-2',
          name: 'Task FS',
          fields: [makeField({ value: 'task-val', order: 1 })],
        }),
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
          apiNameBinding: 'fs-empty',
          name: 'All Empty',
          fields: [
            makeField({ apiName: 'e1', value: '', order: 1 }),
            makeField({ apiName: 'e2', value: '', order: 2 }),
          ],
        }),
        makeFieldset({
          apiNameBinding: 'fs-has-val',
          name: 'Has Value',
          fields: [makeField({ apiName: 'f1', value: 'data', order: 1 })],
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

    it('keeps a User field inside a fieldset that has only groupId set (no value, no userId)', () => {
      const fieldsets = [
        makeFieldset({
          fields: [
            makeField({
              apiName: 'owner-group',
              type: EExtraFieldType.User,
              value: null,
              userId: null,
              groupId: 99,
              order: 1,
            }),
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

      const passedFieldsets = getLastKickoffOutputsProps().fieldsets;
      expect(passedFieldsets).toHaveLength(1);
      expect(passedFieldsets[0].fields).toHaveLength(1);
      expect(passedFieldsets[0].fields[0].apiName).toBe('owner-group');
    });

    it('keeps a fieldset field that has no value but has attachments', () => {
      const fieldsets = [
        makeFieldset({
          fields: [
            makeField({
              apiName: 'doc',
              type: EExtraFieldType.File,
              value: null,
              attachments: [{ id: '1', url: 'doc.pdf', name: 'doc.pdf', size: 10 }],
              order: 1,
            }),
            makeField({
              apiName: 'empty',
              value: '',
              attachments: [],
              order: 2,
            }),
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

      const passedFieldsets = getLastKickoffOutputsProps().fieldsets;
      expect(passedFieldsets).toHaveLength(1);
      expect(passedFieldsets[0].fields).toHaveLength(1);
      expect(passedFieldsets[0].fields[0].apiName).toBe('doc');
    });

    it('shows Ellipsis when total count of outputs + fieldset fields is greater than 1', () => {
      const outputs = [makeField({ apiName: 'plain', value: 'top-value', order: 5 })];
      const fieldsets = [
        makeFieldset({
          fields: [makeField({ apiName: 'inside', value: 'inside-value', order: 1 })],
        }),
      ];

      const props = makeBaseProps({
        type: EWorkflowLogEvent.WorkflowRun,
        workflow: makeWorkflow({
          id: 1,
          description: null,
          output: outputs,
          fieldsets,
        }),
      });

      render(React.createElement(FeedItemHeader, props));

      expect(Ellipsis).toHaveBeenCalled();
      expect(screen.getByRole('button', { name: 'ellipsis' })).toBeInTheDocument();
    });

    it('after Ellipsis click passes isTruncated=false to KickoffOutputs and hides the ellipsis', () => {
      const fieldsets = [
        makeFieldset({
          fields: [
            makeField({ apiName: 'a', value: 'va', order: 1 }),
            makeField({ apiName: 'b', value: 'vb', order: 2 }),
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

      expect(getLastKickoffOutputsProps().isTruncated).toBe(true);

      userEvent.click(screen.getByRole('button', { name: 'ellipsis' }));

      expect(getLastKickoffOutputsProps().isTruncated).toBe(false);
      expect(screen.queryByRole('button', { name: 'ellipsis' })).not.toBeInTheDocument();
    });
  });

  describe('AddedPerformerGroup', () => {
    it('renders group name with added label', () => {
      const item = makeHighlightsItem(EWorkflowLogEvent.AddedPerformerGroup, { targetGroupId: 5 });

      render(React.createElement(FeedItemHeader, item));

      expect(screen.getByText(ADDED_GROUP_LABEL.trim())).toBeInTheDocument();
      expect(screen.getByText(GROUP_NAME)).toBeInTheDocument();
    });

    it('returns null when targetGroupId is missing', () => {
      const item = makeHighlightsItem(EWorkflowLogEvent.AddedPerformerGroup, { targetGroupId: null });

      const { container } = render(React.createElement(FeedItemHeader, item));

      expect(container).toBeEmptyDOMElement();
    });
  });

  describe('RemovedPerformerGroup', () => {
    it('renders group name with removed label', () => {
      const item = makeHighlightsItem(EWorkflowLogEvent.RemovedPerformerGroup, { targetGroupId: 5 });

      render(React.createElement(FeedItemHeader, item));

      expect(screen.getByText(REMOVED_GROUP_LABEL.trim())).toBeInTheDocument();
      expect(screen.getByText(GROUP_NAME)).toBeInTheDocument();
    });

    it('returns null when targetGroupId is missing', () => {
      const item = makeHighlightsItem(EWorkflowLogEvent.RemovedPerformerGroup, { targetGroupId: null });

      const { container } = render(React.createElement(FeedItemHeader, item));

      expect(container).toBeEmptyDOMElement();
    });
  });
});
