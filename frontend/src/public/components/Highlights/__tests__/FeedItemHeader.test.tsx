// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useSelector } from 'react-redux';

import { FeedItemHeader } from '../FeedItemHeader';
import { EWorkflowLogEvent, EWorkflowStatus } from '../../../types/workflow';
import { IHighlightsItem } from '../../../types/highlights';
import { intlMock } from '../../../__stubs__/intlMock';

jest.mock('../../RichText', () => ({
  RichText: ({ text }: { text: string }) => <span>{text}</span>,
}));

jest.mock('../../Attachments', () => ({
  Attachments: () => null,
}));

jest.mock('../../KickoffOutputs', () => ({
  KickoffOutputs: () => null,
  EKickoffOutputsViewModes: { Short: 'short' },
}));

jest.mock('../../UserData', () => ({
  UserData: ({ children }: { children: (user: any) => React.ReactNode }) =>
    children({ id: 1, firstName: 'John', lastName: 'Doe' }),
}));

jest.mock('../../UI', () => ({
  Tooltip: ({ children }: any) => children,
  DateFormat: ({ date }: { date: string }) => <span>{date}</span>,
}));

jest.mock('../../UI/DateFormat', () => ({
  DateFormat: ({ date }: { date: string }) => <span>{date}</span>,
}));

jest.mock('../../../utils/users', () => ({
  getUserFullName: (u: any, opts?: any) =>
    opts?.withAtSign ? `@${u.firstName} ${u.lastName}` : `${u.firstName} ${u.lastName}`,
}));

jest.mock('../../../utils/dateTime', () => ({
  getSnoozedUntilDate: () => '2024-01-01',
}));

jest.mock('../Ellipsis', () => ({
  Ellipsis: () => null,
}));

jest.mock('../utils/TruncatedContent', () => ({
  TruncatedContent: ({ children }: any) => children,
}));

const GROUP_NAME = 'Engineering Team';

const makeHighlightsItem = (
  type: EWorkflowLogEvent,
  overrides: Partial<IHighlightsItem> = {},
): IHighlightsItem => ({
  id: 1,
  type,
  task: {
    id: 10,
    name: 'Test Task',
    number: 1,
    process: 100,
    delay: null,
    output: [],
    dueDate: null,
  },
  text: '',
  attachments: [],
  created: '2024-01-01T00:00:00Z',
  user: { id: 1 },
  workflow: {
    id: 100,
    name: 'Test Workflow',
    currentTask: 1,
    tasksCount: 3,
    template: { id: 1, name: 'Template', count: 0 },
    isLegacyTemplate: false,
    legacyTemplateName: '',
    status: EWorkflowStatus.Running,
    kickoff: null,
    isExternal: false,
  },
  userId: 1,
  targetUserId: null,
  targetGroupId: null,
  delay: null,
  ...overrides,
});

describe('FeedItemHeader', () => {
  const t = (id: string) => intlMock.formatMessage({ id });
  const ADDED_GROUP_LABEL = t('task.log-added-performer-group');
  const REMOVED_GROUP_LABEL = t('task.log-removed-performer-group');

  beforeEach(() => {
    jest.clearAllMocks();
    (useSelector as jest.Mock).mockImplementation((cb: any) =>
      cb({
        authUser: { isSuperuser: false, account: {} },
        groups: {
          list: [{ id: 5, name: GROUP_NAME }],
        },
        accounts: { isCreateUserModalOpen: false },
      }),
    );
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

      expect(container.innerHTML).toBe('');
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

      expect(container.innerHTML).toBe('');
    });
  });
});
