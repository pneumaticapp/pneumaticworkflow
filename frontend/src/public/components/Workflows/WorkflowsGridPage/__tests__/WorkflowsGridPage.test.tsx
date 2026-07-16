import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../../lang/locales/en_US';

import { WorkflowsGridPage } from '../WorkflowsGridPage';
import { getTemplate } from '../../../../api/getTemplate';
import {
  getRunnableWorkflow,
  loadDatasetsMap,
} from '../../../TemplateEdit/utils/getRunnableWorkflow';
import { mapTemplateFieldsetsToRuntime } from '../../../../utils/mapTemplateFieldsetsToRuntime';
import { EWorkflowsLoadingStatus, EWorkflowsView } from '../../../../types/workflow';
import { ITemplateTitle } from '../../../../types/template';
import { intlMock } from '../../../../__stubs__/intlMock';
import { makeFieldsetRuntime } from '../../../../__stubs__/fieldsets.factory';

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    React.createElement(IntlProvider, { locale: 'en', messages: enMessages }, ui),
  );

jest.mock('../../../../api/getTemplate', () => ({
  getTemplate: jest.fn(),
}));

jest.mock('../../../TemplateEdit/utils/getRunnableWorkflow', () => ({
  loadDatasetsMap: jest.fn(),
  getRunnableWorkflow: jest.fn(),
}));

jest.mock('../../../../utils/mapTemplateFieldsetsToRuntime', () => ({
  mapTemplateFieldsetsToRuntime: jest.fn(),
}));

jest.mock('../../../../utils/logger', () => ({
  logger: { error: jest.fn() },
}));

jest.mock('../../../../utils/getErrorMessage', () => ({
  getErrorMessage: jest.fn(() => 'error'),
}));

jest.mock('../../../UI/Notifications', () => ({
  NotificationManager: { notifyApiError: jest.fn() },
}));

jest.mock('../../../UI/Typeography/Header', () => ({
  Header: ({ children }: { children: React.ReactNode }) =>
    React.createElement('span', null, children),
}));

jest.mock('../../../icons', () => ({
  SearchLargeIcon: () => null,
  StartRoundIcon: () => null,
}));

jest.mock('../../../UI', () => ({
  InputField: jest.fn(() => React.createElement('input')),
  Loader: () => null,
}));

jest.mock('../../../PageTitle/PageTitle', () => ({
  PageTitle: () => null,
}));

jest.mock('../WorkflowCard', () => ({
  WorkflowCardContainer: jest.fn(() => null),
}));

jest.mock('../WorkflowCardLoader', () => ({
  WorkflowCardLoader: () => null,
}));

jest.mock('react-infinite-scroll-component', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', null, children),
}));

jest.mock('../../../../utils/helpers', () => {
  const actual = jest.requireActual('../../../../utils/helpers');
  return { isArrayWithItems: actual.isArrayWithItems };
});

const formatMsg = (id: string) => intlMock.formatMessage({ id });
const RUN_WORKFLOW_TEXT = formatMsg('workflows.run-workflow');

const makeTemplateTitle = (overrides: Partial<ITemplateTitle> = {}): ITemplateTitle => ({
  id: 1,
  name: 'Template A',
  count: 0,
  ...overrides,
});

const baseProps = {
  workflowsLoadingStatus: EWorkflowsLoadingStatus.Loaded,
  workflowsList: { count: 0, offset: 0, items: [] },
  templatesFilter: [] as ITemplateTitle[],
  tasksApiNamesFilter: [],
  searchText: '',
  view: EWorkflowsView.Grid,
  onSearch: jest.fn(),
  setTasksFilter: jest.fn(),
  openRunWorkflowModal: jest.fn(),
  loadWorkflowsList: jest.fn(),
  openWorkflowLogPopup: jest.fn(),
  loadTemplatesTitles: jest.fn(),
  resetWorkflows: jest.fn(),
  openSelectTemplateModal: jest.fn(),
  removeWorkflowFromList: jest.fn(),
};

const fakeTemplate = {
  id: 1,
  name: 'Template A',
  kickoff: { description: '', fields: [], fieldsets: [] },
  description: '',
  isActive: true,
  tasks: [],
  wfNameTemplate: null,
};

const fakeRunnable = { id: 1, name: 'Template A', kickoff: { description: '', fields: [] } };
const fakeFieldsets = [makeFieldsetRuntime({ apiNameBinding: 'fs-1', name: 'FS' })];
const fakeDatasetsMap = {};

describe('WorkflowsGridPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const clickRunButton = () => {
    const buttons = screen.getAllByRole('button');
    const runBtn = buttons.find((btn) => btn.textContent?.includes(RUN_WORKFLOW_TEXT)
      || btn.textContent?.includes('Template'));
    if (!runBtn) throw new Error('Run Workflow button not found');
    userEvent.click(runBtn);
  };

  describe('Fieldsets: loading orchestration on Run Workflow', () => {
    it('calls the full fieldsets loading chain when a single template is in the filter', async () => {
      (getTemplate as jest.Mock).mockResolvedValue(fakeTemplate);
      (mapTemplateFieldsetsToRuntime as jest.Mock).mockReturnValue({
        normalizedTemplate: fakeTemplate,
        loadedFieldsets: fakeFieldsets,
      });
      (loadDatasetsMap as jest.Mock).mockResolvedValue(fakeDatasetsMap);
      (getRunnableWorkflow as jest.Mock).mockReturnValue(fakeRunnable);

      renderWithIntl(
        React.createElement(WorkflowsGridPage, {
          ...baseProps,
          templatesFilter: [makeTemplateTitle({ id: 42 })],
        }),
      );

      clickRunButton();

      await waitFor(() => {
        expect(baseProps.openRunWorkflowModal).toHaveBeenCalledTimes(1);
      });

      expect(getTemplate).toHaveBeenCalledTimes(1);
      expect(getTemplate).toHaveBeenCalledWith(42);

      expect(mapTemplateFieldsetsToRuntime).toHaveBeenCalledTimes(1);
      expect(mapTemplateFieldsetsToRuntime).toHaveBeenCalledWith(fakeTemplate);

      expect(loadDatasetsMap).toHaveBeenCalledTimes(1);
      expect(loadDatasetsMap).toHaveBeenCalledWith(fakeTemplate.kickoff, fakeFieldsets);

      expect(getRunnableWorkflow).toHaveBeenCalledTimes(1);
      expect(getRunnableWorkflow).toHaveBeenCalledWith(fakeTemplate, fakeDatasetsMap, fakeFieldsets);

      expect(baseProps.openRunWorkflowModal).toHaveBeenCalledWith(fakeRunnable);
    });

    it('opens SelectTemplateModal without loading fieldsets when filter is empty', () => {
      renderWithIntl(
        React.createElement(WorkflowsGridPage, {
          ...baseProps,
          templatesFilter: [],
        }),
      );

      clickRunButton();

      expect(baseProps.openSelectTemplateModal).toHaveBeenCalledTimes(1);
      expect(mapTemplateFieldsetsToRuntime).not.toHaveBeenCalled();
      expect(getTemplate).not.toHaveBeenCalled();
    });

    it('opens SelectTemplateModal with ids without loading fieldsets when multiple templates are in the filter', () => {
      renderWithIntl(
        React.createElement(WorkflowsGridPage, {
          ...baseProps,
          templatesFilter: [makeTemplateTitle({ id: 1 }), makeTemplateTitle({ id: 2 })],
        }),
      );

      clickRunButton();

      expect(baseProps.openSelectTemplateModal).toHaveBeenCalledTimes(1);
      expect(baseProps.openSelectTemplateModal).toHaveBeenCalledWith(
        expect.objectContaining({ templatesIdsFilter: [1, 2] }),
      );
      expect(mapTemplateFieldsetsToRuntime).not.toHaveBeenCalled();
    });

    it('falls back to SelectTemplateModal when getTemplate returns null', async () => {
      (getTemplate as jest.Mock).mockResolvedValue(null);

      renderWithIntl(
        React.createElement(WorkflowsGridPage, {
          ...baseProps,
          templatesFilter: [makeTemplateTitle({ id: 1 })],
        }),
      );

      clickRunButton();

      await waitFor(() => {
        expect(baseProps.openSelectTemplateModal).toHaveBeenCalledTimes(1);
      });

      expect(mapTemplateFieldsetsToRuntime).not.toHaveBeenCalled();
      expect(baseProps.openRunWorkflowModal).not.toHaveBeenCalled();
    });
  });
});
