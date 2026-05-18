// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { intlMock } from '../../../../__stubs__/intlMock';
import { history } from '../../../../utils/history';
import { TemplateControlls, ITemplateControllsProps } from '../TemplateControlls';
import { ERoutes } from '../../../../constants/routes';
import { ETemplateStatus } from '../../../../types/redux';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn() },
  isCreateTemplate: jest.fn(() => false),
  checkSomeRouteMatchesLocation: jest.fn(() => false),
}));

jest.mock('react-router-dom', () => ({
  Link: ({ children }: any) => children,
}));

jest.mock('rc-switch', () => ({ __esModule: true, default: () => null }));

jest.mock('../../../icons', () => ({
  ActivityIcon: () => null,
  BoxesIcon: () => null,
  EnableIcon: () => null,
  TrashIcon: () => null,
  UnionIcon: () => null,
  WarningIcon: () => null,
}));

jest.mock('../../../IntlMessages', () => ({
  IntlMessages: () => null,
}));

jest.mock('../../../UI/ShowMore', () => ({
  ShowMore: () => null,
}));

jest.mock('../../../UI/Buttons/Button', () => ({
  Button: () => null,
}));

jest.mock('../../../UI/WarningPopup', () => ({
  WarningPopup: () => null,
}));

jest.mock('../../../UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

jest.mock('../../../UI', () => ({
  RouteLeavingGuard: () => null,
}));

jest.mock('../../TemplateOwners', () => ({
  TemplateOwners: () => null,
}));

jest.mock('../../TemplateViewers', () => ({
  TemplateViewers: () => null,
}));

jest.mock('../../TemplateStarters', () => ({
  TemplateStarters: () => null,
}));

jest.mock('../../../TemplateIntegrationsStats', () => ({
  useTemplateIntegrationsList: jest.fn(() => []),
}));

jest.mock('../../../Templates', () => ({
  checkShowDraftTemplateWarning: jest.fn(() => false),
}));

jest.mock('../../utils/getRunnableWorkflow', () => ({
  getRunnableWorkflow: jest.fn(),
  loadDatasetsMap: jest.fn(),
  loadFieldsetsData: jest.fn(),
}));

jest.mock('../../utils/validateTemplate', () => ({
  validateTemplate: jest.fn(() => ({ commonWarnings: [], infoWarnings: [] })),
}));

jest.mock('../../../../utils/routes/getLinkToWorkflows', () => ({
  getLinkToWorkflows: jest.fn(() => '/'),
}));

jest.mock('../../../../utils/routes/getLinkToHighlightsByTemplate', () => ({
  getLinkToHighlightsByTemplate: jest.fn(() => '/'),
}));

const makeTemplate = (id: number | undefined) => ({
  id,
  name: 'Test Template',
  owners: [],
  isActive: true,
  isPublic: false,
  finalizable: false,
  completionNotification: false,
  reminderNotification: false,
  kickoff: { description: '', fields: [], fieldsets: [] },
  tasks: [],
  fieldsets: [],
} as any);

describe('TemplateControlls — fieldset logic', () => {
  const makeProps = (overrides: Partial<ITemplateControllsProps> = {}): ITemplateControllsProps => ({
    template: makeTemplate(10),
    templateStatus: ETemplateStatus.Saved,
    isSubscribed: false,
    cloneTemplate: jest.fn(),
    patchTemplate: jest.fn(),
    deleteTemplate: jest.fn(),
    openRunWorkflowModal: jest.fn(),
    setInfoWarnings: jest.fn(),
    ...overrides,
  });

  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders button with text template.more-show-fieldsets', () => {
    render(React.createElement(TemplateControlls, makeProps()));

    expect(
      screen.getByRole('button', { name: formatMsg('template.more-show-fieldsets') }),
    ).toBeInTheDocument();
  });

  it('click with templateId=10 calls history.push once with fieldsets route', () => {
    render(React.createElement(TemplateControlls, makeProps({ template: makeTemplate(10) })));

    userEvent.click(
      screen.getByRole('button', { name: formatMsg('template.more-show-fieldsets') }),
    );

    const expectedUrl = ERoutes.TemplateFieldsets.replace(':templateId', '10');
    expect(history.push).toHaveBeenCalledTimes(1);
    expect(history.push).toHaveBeenCalledWith(expectedUrl);
  });

  it('click without templateId calls patchTemplate once with changedFields: {}', () => {
    const patchTemplate = jest.fn();

    render(
      React.createElement(
        TemplateControlls,
        makeProps({ template: makeTemplate(undefined), patchTemplate }),
      ),
    );

    userEvent.click(
      screen.getByRole('button', { name: formatMsg('template.more-show-fieldsets') }),
    );

    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect(patchTemplate).toHaveBeenCalledWith(
      expect.objectContaining({ changedFields: {} }),
    );
  });
});
