// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';

import { FeedItemHeader } from '../FeedItemHeader';
import { KickoffOutputs } from '../../KickoffOutputs';
import { EWorkflowLogEvent, EWorkflowStatus } from '../../../types/workflow';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../types/template';
import { IHighlightsItem } from '../../../types/highlights';

jest.mock('../../KickoffOutputs', () => ({
  KickoffOutputs: jest.fn(() => null),
  EKickoffOutputsViewModes: { Short: 'short', Detailed: 'detailed' },
}));

jest.mock('../../RichText', () => ({ RichText: () => null }));
jest.mock('../../Attachments', () => ({ Attachments: () => null }));
jest.mock('../../UserData', () => ({ UserData: () => null }));
jest.mock('../Ellipsis', () => ({ Ellipsis: () => null }));
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
});
