// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { FeedItem, ALLOWED_EVENT_TYPES } from '../FeedItem';
import { EWorkflowLogEvent, EWorkflowStatus } from '../../../types/workflow';
import { IHighlightsItem } from '../../../types/highlights';

jest.mock('../FeedItemHeader', () => ({
  FeedItemHeader: () => <div data-testid="feed-header" />,
}));

jest.mock('../FeedItemIcon', () => ({
  FeedItemIcon: () => <div data-testid="feed-icon" />,
}));

jest.mock('../../UserData', () => ({
  UserData: ({ children }: { children: (user: any) => React.ReactNode }) =>
    children({ id: 1, firstName: 'John', lastName: 'Doe' }),
}));

jest.mock('../../UI', () => ({
  Dropdown: () => null,
  Loader: () => null,
}));

jest.mock('../../icons', () => ({
  EditIcon: () => null,
  MoreIcon: () => null,
}));

jest.mock('../../../utils/users', () => ({
  getUserFullName: (u: any) => `${u.firstName} ${u.lastName}`,
  EXTERNAL_USER: { firstName: 'External', lastName: 'User' },
}));

jest.mock('react-router-dom', () => ({
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

jest.mock('../../UI/DateFormat', () => ({
  DateFormat: ({ date }: { date: string }) => <span>{date}</span>,
}));

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

describe('FeedItem', () => {
  const baseProps = {
    applyUserFilter: jest.fn(() => jest.fn()),
    applyTemplatesFilter: jest.fn(() => jest.fn()),
    isProcessLogPopupLoading: false,
    openProcessLogPopup: jest.fn(),
    redirectToTemplate: jest.fn(() => jest.fn()),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('ALLOWED_EVENT_TYPES', () => {
    it('includes AddedPerformerGroup', () => {
      expect(ALLOWED_EVENT_TYPES).toContain(EWorkflowLogEvent.AddedPerformerGroup);
    });

    it('includes RemovedPerformerGroup', () => {
      expect(ALLOWED_EVENT_TYPES).toContain(EWorkflowLogEvent.RemovedPerformerGroup);
    });
  });

  describe('render', () => {
    it('renders AddedPerformerGroup event', () => {
      const item = makeHighlightsItem(EWorkflowLogEvent.AddedPerformerGroup, { targetGroupId: 5 });

      render(React.createElement(FeedItem, { ...baseProps, ...item, item }));

      expect(screen.getByTestId('feed-header')).toBeInTheDocument();
      expect(screen.getByTestId('feed-icon')).toBeInTheDocument();
    });

    it('renders RemovedPerformerGroup event', () => {
      const item = makeHighlightsItem(EWorkflowLogEvent.RemovedPerformerGroup, { targetGroupId: 5 });

      render(React.createElement(FeedItem, { ...baseProps, ...item, item }));

      expect(screen.getByTestId('feed-header')).toBeInTheDocument();
      expect(screen.getByTestId('feed-icon')).toBeInTheDocument();
    });
  });
});
