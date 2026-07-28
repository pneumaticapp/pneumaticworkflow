import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';
import { IntlProvider } from 'react-intl';
import { MemoryRouter } from 'react-router-dom';

import { Templates } from '../Templates';
import { ETemplatesSorting } from '../../../types/workflow';
import { ETemplatesSystemStatus } from '../../../redux/actions';
import { enMessages } from '../../../lang/locales/en_US';
import {
  loadTemplates,
  loadTemplatesSystem,
  loadTemplatesSystemCategories,
} from '../../../redux/actions';
import { INIT_STATE as INIT_TEMPLATES_STATE } from '../../../redux/templates/reducer';

jest.mock('../../../constants/enviroment', () => ({
  isEnvAi: false,
}));

const createMockState = ({ isAdmin }: { isAdmin: boolean }) => ({
  authUser: {
    isAdmin,
  },
  templates: {
    ...INIT_TEMPLATES_STATE,
    templatesList: {
      count: 0,
      offset: 0,
      items: [],
    },
    templatesListSorting: ETemplatesSorting.DateDesc,
    systemTemplates: {
      ...INIT_TEMPLATES_STATE.systemTemplates,
      status: ETemplatesSystemStatus.WaitingForAction,
    },
  },
});

const renderTemplates = () =>
  render(
    <MemoryRouter>
      <IntlProvider locale="en" messages={enMessages}>
        <Templates />
      </IntlProvider>
    </MemoryRouter>,
  );

describe('Templates', () => {
  const mockDispatch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  it('loads system templates for admin', () => {
    (useSelector as jest.Mock).mockImplementation((selector) => selector(createMockState({ isAdmin: true })));

    renderTemplates();

    expect(mockDispatch).toHaveBeenCalledWith(loadTemplates(0));
    expect(mockDispatch).toHaveBeenCalledWith(loadTemplatesSystem());
    expect(mockDispatch).toHaveBeenCalledWith(loadTemplatesSystemCategories());
    expect(screen.getByText('Explore Workflow Template Examples')).toBeInTheDocument();
    expect(screen.getByText('New Template')).toBeInTheDocument();
  });

  it('does not load or show system templates for non-admin', () => {
    (useSelector as jest.Mock).mockImplementation((selector) => selector(createMockState({ isAdmin: false })));

    renderTemplates();

    expect(mockDispatch).toHaveBeenCalledWith(loadTemplates(0));
    expect(mockDispatch).not.toHaveBeenCalledWith(loadTemplatesSystem());
    expect(mockDispatch).not.toHaveBeenCalledWith(loadTemplatesSystemCategories());
    expect(screen.queryByText('Explore Workflow Template Examples')).not.toBeInTheDocument();
    expect(screen.queryByText('New Template')).not.toBeInTheDocument();
  });
});
