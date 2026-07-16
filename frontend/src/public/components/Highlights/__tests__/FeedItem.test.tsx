// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { FeedItem, ALLOWED_EVENT_TYPES } from '../FeedItem';
import { EWorkflowLogEvent } from '../../../types/workflow';
import { makeHighlightsItem } from '../../../__stubs__/highlights.factory';

jest.mock('../FeedItemHeader', () => ({
  FeedItemHeader: () => <div data-testid="feed-header" />,
}));

jest.mock('../FeedItemIcon', () => ({
  FeedItemIcon: () => <div data-testid="feed-icon" />,
}));

jest.mock('../../UserData', () => ({
  UserData: ({ children }: { children: (user: { id: number; firstName: string; lastName: string }) => React.ReactNode }) =>
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
  getUserFullName: (user: { firstName: string; lastName: string }) => `${user.firstName} ${user.lastName}`,
  EXTERNAL_USER: { firstName: 'External', lastName: 'User' },
}));

jest.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => <a href={to}>{children}</a>,
}));

jest.mock('../../UI/DateFormat', () => ({
  DateFormat: ({ date }: { date: string }) => <span>{date}</span>,
}));

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
