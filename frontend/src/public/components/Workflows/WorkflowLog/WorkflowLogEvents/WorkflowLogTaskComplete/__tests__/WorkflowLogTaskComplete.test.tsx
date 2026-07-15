import React from 'react';
import type { ReactNode } from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { WorkflowLogTaskComplete } from '../WorkflowLogTaskComplete';

jest.mock('../../../../../UserData', () => ({
  UserData: ({ children }: { children(user: unknown): ReactNode }) => children({ firstName: 'Test', lastName: 'User' }),
}));

jest.mock('../../../../../KickoffOutputs', () => ({
  EKickoffOutputsViewModes: { Short: 'short' },
  KickoffOutputs: () => <div data-testid="outputs" />,
}));

jest.mock('../../../../../UI/Avatar', () => ({
  Avatar: () => <div />,
}));

jest.mock('../../../../../UI/DateFormat', () => ({
  DateFormat: () => <span />,
}));

describe('WorkflowLogTaskComplete', () => {
  it('does not crash when completed task has no output', () => {
    render(
      <IntlProvider locale="en" messages={{ 'workflows.log-complete': 'Completed {taskName}' }}>
        <WorkflowLogTaskComplete
          userId={1}
          created="2024-01-01T00:00:00Z"
          currentTask={{ name: 'Task without output' } as any}
        />
      </IntlProvider>,
    );

    expect(screen.queryByTestId('outputs')).not.toBeInTheDocument();
  });
});
