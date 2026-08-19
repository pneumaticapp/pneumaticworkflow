import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { WorkflowLogWorkflowFinished } from '../WorkflowLogWorkflowFinished';
import { enMessages } from '../../../../../../lang/locales/en_US';
import { EWorkflowLogEvent } from '../../../../../../types/workflow';

jest.mock('../../../../../UserData', () => ({
  UserData: jest.fn(({ children }: { children: (user: Record<string, string> | null) => React.ReactNode }) =>
    children({ id: '1', firstName: 'Test', lastName: 'User', email: 'test@test.com' }),
  ),
}));

jest.mock('../../../../../UI/Avatar', () => ({
  Avatar: ({ isSystemAvatar }: { isSystemAvatar?: boolean }) => (
    <div data-testid={isSystemAvatar ? 'system-avatar' : 'user-avatar'} />
  ),
}));

jest.mock('../../../../../icons', () => ({
  WorkflowEndedIcon: () => null,
}));

jest.mock('../../../../../UI/DateFormat', () => ({
  DateFormat: () => 'mocked-date',
}));

jest.mock('../../../../../../utils/users', () => ({
  getUserFullName: jest.fn(() => 'Test User'),
}));

const renderWithIntl = (ui: React.ReactElement) =>
  render(React.createElement(IntlProvider, { locale: 'en', messages: enMessages }, ui));

describe('WorkflowLogWorkflowFinished', () => {
  it('shows user for workflow complete event', () => {
    renderWithIntl(
      <WorkflowLogWorkflowFinished userId={1} created="2024-01-01" type={EWorkflowLogEvent.WorkflowComplete} />,
    );

    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByTestId('user-avatar')).toBeInTheDocument();
  });

  it('shows system actor for automatic workflow finished event', () => {
    renderWithIntl(
      <WorkflowLogWorkflowFinished userId={1} created="2024-01-01" type={EWorkflowLogEvent.WorkflowFinished} />,
    );

    expect(screen.getByText('Pneumatic')).toBeInTheDocument();
    expect(screen.queryByText('Test User')).not.toBeInTheDocument();
    expect(screen.getByTestId('system-avatar')).toBeInTheDocument();
  });
});
