// <reference types="jest" />
import * as React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { intlMock } from '../../../../__stubs__/intlMock';
import { history } from '../../../../utils/history';
import { TemplateControlls, ITemplateControllsProps } from '../TemplateControlls';
import { ERoutes } from '../../../../constants/routes';
import { ETemplateStatus } from '../../../../types/redux';
import { RouteLeavingGuard } from '../../../UI';
import {
  getRunnableWorkflow,
  loadDatasetsMap,
  loadFieldsetsData,
} from '../../utils/getRunnableWorkflow';
import { discardTemplateChanges } from '../../../../redux/actions';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn() },
  isCreateTemplate: jest.fn(() => false),
  checkSomeRouteMatchesLocation: jest.fn(() => false),
}));

jest.mock('../../../../redux/actions', () => ({
  discardTemplateChanges: jest.fn((p) => ({ type: 'template/discardChanges', payload: p })),
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

  it('after a successful draft patch, onSuccess redirects to the fieldsets page using the new id from the URL', () => {
    const patchTemplate = jest.fn();

    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { pathname: '/templates/edit/42' },
    });

    try {
      render(
        React.createElement(
          TemplateControlls,
          makeProps({ template: makeTemplate(undefined), patchTemplate }),
        ),
      );

      userEvent.click(
        screen.getByRole('button', { name: formatMsg('template.more-show-fieldsets') }),
      );

      const onSuccess = (patchTemplate.mock.calls[0][0] as { onSuccess: () => void }).onSuccess;
      onSuccess();

      const expectedUrl = ERoutes.TemplateFieldsets.replace(':templateId', '42');
      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(expectedUrl);
    } finally {
      Object.defineProperty(window, 'location', { writable: true, value: originalLocation });
    }
  });

  it('clicking Run on an active saved template runs the chain loadFieldsets → loadDatasets → getRunnable → openModal', async () => {
    const openRunWorkflowModal = jest.fn();
    const loadedFieldsets = [{ apiName: 'fs-1' }] as any[];
    const datasetsMap = { ds1: ['v1'] } as any;
    const runnableWorkflow = { kickoff: {}, tasks: [] } as any;

    (loadFieldsetsData as jest.Mock).mockResolvedValue(loadedFieldsets);
    (loadDatasetsMap as jest.Mock).mockResolvedValue(datasetsMap);
    (getRunnableWorkflow as jest.Mock).mockReturnValue(runnableWorkflow);

    const template = makeTemplate(10);
    template.isActive = true;

    render(
      React.createElement(
        TemplateControlls,
        makeProps({ template, openRunWorkflowModal, templateStatus: ETemplateStatus.Saved }),
      ),
    );

    userEvent.click(screen.getByRole('button', { name: formatMsg('templates.run-workflow') }));

    await waitFor(() => expect(openRunWorkflowModal).toHaveBeenCalledTimes(1));

    expect(loadFieldsetsData).toHaveBeenCalledTimes(1);
    expect(loadFieldsetsData).toHaveBeenCalledWith(template.kickoff, 10);

    expect(loadDatasetsMap).toHaveBeenCalledTimes(1);
    expect(loadDatasetsMap).toHaveBeenCalledWith(template.kickoff, loadedFieldsets);

    expect(getRunnableWorkflow).toHaveBeenCalledTimes(1);
    expect(getRunnableWorkflow).toHaveBeenCalledWith(template, datasetsMap, loadedFieldsets);

    expect(openRunWorkflowModal).toHaveBeenCalledWith(runnableWorkflow);
  });

  it('after Discard, calling onReject with a fieldsets path redirects to /templates/ instead of fieldsets', () => {
    const mockDispatch = jest.fn();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);

    const template = makeTemplate(1);
    template.isActive = false;

    render(React.createElement(TemplateControlls, makeProps({ template })));

    userEvent.click(
      screen.getByRole('button', { name: formatMsg('templates.discard-changes') }),
    );

    const guardMock = RouteLeavingGuard as unknown as jest.Mock;
    const lastProps = guardMock.mock.calls[guardMock.mock.calls.length - 1][0];
    const onReject = lastProps.onReject as (path: string) => void;

    act(() => {
      onReject('/templates/1/fieldsets/');
    });

    expect(history.push).toHaveBeenCalledTimes(1);
    expect(history.push).toHaveBeenCalledWith(ERoutes.Templates);

    expect(discardTemplateChanges).toHaveBeenCalledTimes(1);
    expect(discardTemplateChanges).toHaveBeenCalledWith(
      expect.objectContaining({ templateId: 1 }),
    );
  });
});
