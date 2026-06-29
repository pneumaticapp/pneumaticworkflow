import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { intlMock } from '../../../../__stubs__/intlMock';
import { TemplateControlls, ITemplateControllsProps } from '../TemplateControlls';
import { ETemplateStatus } from '../../../../types/redux';
import {
  getRunnableWorkflow,
  loadDatasetsMap,
} from '../../utils/getRunnableWorkflow';
import { mapFieldsetBindingClientToRuntime } from '../../../../utils/mapFieldsetBindingClientToRuntime';
import { getTemplate } from '../../../../__stubs__/templates';
import { makeFieldsetBindingClient } from '../../../../__stubs__/fieldsets.factory';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn() },
  isCreateTemplate: jest.fn(() => false),
  checkSomeRouteMatchesLocation: jest.fn(() => false),
}));

jest.mock('../../../../redux/actions', () => ({
  discardTemplateChanges: jest.fn((p) => ({ type: 'template/discardChanges', payload: p })),
}));

jest.mock('react-router-dom', () => ({
  Link: ({ children }: { children: React.ReactNode }) => children,
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
  Button: jest.fn(
    (props: { label: string; onClick?: () => void; disabled?: boolean }) =>
      React.createElement(
        'button',
        { type: 'button', onClick: props.onClick, disabled: props.disabled },
        props.label,
      ),
  ),
}));

jest.mock('../../../UI/WarningPopup', () => ({
  WarningPopup: () => null,
}));

jest.mock('../../../UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

jest.mock('../../../UI', () => ({
  RouteLeavingGuard: jest.fn(
    (props: {
      onConfirm: (path: string) => void;
      onReject: (path: string) => void;
      renderControlls: (confirm: (p: string) => void, reject: (p: string) => void) => React.ReactNode;
    }) => props.renderControlls(props.onConfirm, props.onReject),
  ),
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
}));

jest.mock('../../../../utils/mapFieldsetBindingClientToRuntime', () => ({
  mapFieldsetBindingClientToRuntime: jest.fn(),
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

describe('TemplateControlls — fieldset logic', () => {
  const makeProps = (overrides: Partial<ITemplateControllsProps> = {}) => ({
    template: getTemplate('5'),
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


  it('clicking Run on an active saved template runs the chain mapFieldsets → loadDatasets → getRunnable → openModal', async () => {
    const openRunWorkflowModal = jest.fn();
    const runnableWorkflow = { kickoff: {}, tasks: [] };

    (mapFieldsetBindingClientToRuntime as jest.Mock).mockReturnValue({ apiName: 'fs-1', apiNameBinding: 'fs-1', fields: [] });
    (loadDatasetsMap as jest.Mock).mockResolvedValue({});
    (getRunnableWorkflow as jest.Mock).mockReturnValue(runnableWorkflow);

    const template = getTemplate('5');
    template.isActive = true;
    template.kickoff = {
      description: '',
      fields: [],
      fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1' })],
    };

    render(
      React.createElement(
        TemplateControlls,
        makeProps({ template, openRunWorkflowModal, templateStatus: ETemplateStatus.Saved }),
      ),
    );

    userEvent.click(screen.getByRole('button', { name: formatMsg('templates.run-workflow') }));

    await waitFor(() => expect(openRunWorkflowModal).toHaveBeenCalledTimes(1));


    expect(loadDatasetsMap).toHaveBeenCalledTimes(1);
    expect(loadDatasetsMap).toHaveBeenCalledWith(
      template.kickoff,
      [{ apiName: 'fs-1', apiNameBinding: 'fs-1', fields: [] }],
    );

    expect(getRunnableWorkflow).toHaveBeenCalledTimes(1);
    expect(getRunnableWorkflow).toHaveBeenCalledWith(
      template,
      {},
      [{ apiName: 'fs-1', apiNameBinding: 'fs-1', fields: [] }],
    );
    expect(openRunWorkflowModal).toHaveBeenCalledWith(runnableWorkflow);
  });


});
