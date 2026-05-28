import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { NotificationsList, INotificationsListProps } from '../NotificationsList';
import { TNotificationsListItem } from '../../../types';
import { intlMock } from '../../../__stubs__/intlMock';

jest.mock('react-dom', () => {
  const actual = jest.requireActual('react-dom');
  return {
    ...actual,
    default: { ...actual.default, createPortal: (el: React.ReactNode) => el },
  };
});

jest.mock('react-outside-click-handler', () => {
  return {
    __esModule: true,
    default: ({ children }: { children: React.ReactNode }) => children,
  };
});

jest.mock('react-infinite-scroll-component', () => {
  return {
    __esModule: true,
    default: ({ children }: { children: React.ReactNode }) => children,
  };
});

jest.mock('../../NavLink', () => ({
  NavLink: ({ children, to }: { children: React.ReactNode; to: string }) =>
    React.createElement('a', { href: to, 'data-testid': 'nav-link' }, children),
}));

jest.mock('../../UI/Avatar', () => ({
  Avatar: () => null,
}));

jest.mock('../../UI/Loader', () => ({
  Loader: () => null,
}));

jest.mock('../../RichText', () => ({
  RichText: () => null,
}));

jest.mock('../../UI', () => ({
  Placeholder: () => null,
  SectionTitle: ({ children }: { children: React.ReactNode }) => React.createElement('div', null, children),
}));

jest.mock('../../icons', () => {
  const stub = () => null;
  return {
    ClearIcon: stub,
    CommentInfoIcon: stub,
    PneumaticAvatarIcon: stub,
    UrgentColorIcon: stub,
    NotUrgentIcon: stub,
    AlarmIcon: stub,
    AlarmCrossedIcon: stub,
    TaskCompleteIcon: stub,
    TrashIcon: stub,
  };
});

jest.mock('../../UserData/utils/getUserById', () => ({
  getUserById: jest.fn(),
}));

jest.mock('../../../utils/helpers', () => {
  const actual = jest.requireActual('../../../utils/helpers');
  return { isArrayWithItems: actual.isArrayWithItems };
});

jest.mock('../../../utils/users', () => ({
  getUserFullName: jest.fn(() => ''),
}));

jest.mock('../../../utils/routes', () => ({
  getTaskDetailRoute: jest.fn((id: number) => `/tasks/${id}`),
  getWorkflowDetailedRoute: jest.fn((id: number) => `/workflows/${id}`),
}));

jest.mock('../../../utils/reactElementToText', () => ({
  reactElementToText: jest.fn(() => ''),
}));

jest.mock('../../UI/DateFormat', () => ({
  DateFormat: () => null,
}));

describe('NotificationsList', () => {
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const WORKFLOW_COMPLETED_TEXT = formatMsg('notifications.workflow-completed');
  const PNEUMATIC_TITLE = formatMsg('general.pneumatic');

  const makeCompleteWorkflowNotification = (
    overrides: Partial<TNotificationsListItem> = {},
  ): TNotificationsListItem => ({
    id: 1,
    status: 'new',
    datetime: '2026-05-11T05:01:30.049960Z',
    type: 'complete_workflow',
    workflow: {
      id: 34,
      name: 'Test Workflow',
    },
    ...overrides,
  } as TNotificationsListItem);

  const baseProps: INotificationsListProps = {
    users: [],
    notifications: [],
    isLoading: false,
    withPaywall: false,
    totalNotificationsCount: 0,
    isClosing: false,
    setNotificationsListIsOpen: jest.fn(),
    removeNotificationItem: jest.fn(),
    changeNotificationsList: jest.fn(),
    fetchNotificationsAsRead: jest.fn(),
    markNotificationsAsRead: jest.fn(),
    loadNotificationsList: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('complete_workflow notification rendering', () => {
    it('renders workflow name, "Workflow completed" text and Pneumatic title', () => {
      const notification = makeCompleteWorkflowNotification({
        workflow: { id: 34, name: 'My Important Process' },
      });

      render(
        React.createElement(NotificationsList, {
          ...baseProps,
          notifications: [notification],
          totalNotificationsCount: 1,
        }),
      );

      expect(screen.getByText('My Important Process')).toBeInTheDocument();
      expect(screen.getByText(WORKFLOW_COMPLETED_TEXT)).toBeInTheDocument();
      expect(screen.getByText(PNEUMATIC_TITLE)).toBeInTheDocument();
    });

    it('links to the workflow detail page', () => {
      const notification = makeCompleteWorkflowNotification({
        workflow: { id: 42, name: 'Linked Workflow' },
      });

      render(
        React.createElement(NotificationsList, {
          ...baseProps,
          notifications: [notification],
          totalNotificationsCount: 1,
        }),
      );

      const link = screen.getByTestId('nav-link');
      expect(link).toHaveAttribute('href', '/workflows/42');
    });
  });
});
