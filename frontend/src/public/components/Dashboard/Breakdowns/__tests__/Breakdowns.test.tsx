import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { Breakdowns, IBreakdownsProps } from '../Breakdowns';
import { EDashboardModes } from '../../../../types/redux';

const getProps = (): IBreakdownsProps => ({
  mode: EDashboardModes.Workflows,
  isLoading: false,
  settingsChanged: false,
  openSelectTemplateModal: jest.fn(),
  breakdownItems: [],
  loadBreakdownTasks: jest.fn(),
  openRunWorkflowModalOnDashboard: jest.fn(),
});

describe('Breakdowns', () => {
  it('Renders placeholder if no breakdown items passed', () => {
    const props = getProps();

    render(<Breakdowns {...props} />);

    expect(screen.getByText(/You don't have data to display yet/)).toBeInTheDocument();
  });
})
