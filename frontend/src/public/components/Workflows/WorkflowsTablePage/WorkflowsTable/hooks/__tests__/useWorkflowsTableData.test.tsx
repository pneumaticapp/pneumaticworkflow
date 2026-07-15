import React from 'react';
import { render } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { useSelector } from 'react-redux';

import { getCurrentUser } from '../../../../../../redux/selectors/authUser';
import {
  getLastLoadedTemplateIdForTable,
  getSavedFields,
} from '../../../../../../redux/selectors/workflows';
import { IWorkflowsList } from '../../../../../../types/redux';
import { EExtraFieldType } from '../../../../../../types/template';
import { EWorkflowsLoadingStatus } from '../../../../../../types/workflow';
import { useWorkflowsTableData } from '../useWorkflowsTableData';

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useSelector: jest.fn(),
}));

let hookResult: ReturnType<typeof useWorkflowsTableData>;
let lastLoadedTemplateId: number | null = 1;

const makeWorkflowsList = (fieldApiName: string): IWorkflowsList => ({
  count: 1,
  offset: 0,
  items: [{
    id: 1,
    fields: [{
      apiName: fieldApiName,
      name: fieldApiName,
      type: EExtraFieldType.String,
      value: '',
    }],
  }] as IWorkflowsList['items'],
});

const HookHarness = ({
  templateId,
  workflowsList,
  workflowsLoadingStatus,
}: {
  templateId: number;
  workflowsList: IWorkflowsList;
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
}) => {
  hookResult = useWorkflowsTableData({
    workflowsList,
    workflowsLoadingStatus,
    templatesIdsFilter: [templateId],
    searchHeader: <div />,
    renderWorkflowColumn: () => <div />,
  });

  return null;
};

describe('useWorkflowsTableData', () => {
  beforeEach(() => {
    lastLoadedTemplateId = 1;
    localStorage.clear();
    (useSelector as jest.Mock).mockImplementation((selector) => {
      if (selector === getCurrentUser) {
        return { id: 1 };
      }
      if (selector === getSavedFields) {
        return ['system-column-workflow'];
      }
      if (selector === getLastLoadedTemplateIdForTable) {
        return lastLoadedTemplateId;
      }

      return undefined;
    });
  });

  it('keeps template skeleton columns until the new workflow request completes', () => {
    const oldWorkflows = makeWorkflowsList('old-field');
    const { rerender } = render(
      <IntlProvider locale="en">
        <HookHarness
          templateId={1}
          workflowsList={oldWorkflows}
          workflowsLoadingStatus={EWorkflowsLoadingStatus.Loaded}
        />
      </IntlProvider>,
    );

    rerender(
      <IntlProvider locale="en">
        <HookHarness
          templateId={2}
          workflowsList={oldWorkflows}
          workflowsLoadingStatus={EWorkflowsLoadingStatus.LoadingList}
        />
      </IntlProvider>,
    );

    expect(hookResult.shouldSkeletonOptionalTable).toBe(true);

    lastLoadedTemplateId = 2;
    rerender(
      <IntlProvider locale="en">
        <HookHarness
          templateId={2}
          workflowsList={oldWorkflows}
          workflowsLoadingStatus={EWorkflowsLoadingStatus.LoadingList}
        />
      </IntlProvider>,
    );

    expect(hookResult.shouldSkeletonOptionalTable).toBe(true);
    expect(hookResult.columns.some((column) => column.accessor === 'old-field')).toBe(true);

    rerender(
      <IntlProvider locale="en">
        <HookHarness
          templateId={2}
          workflowsList={makeWorkflowsList('new-field')}
          workflowsLoadingStatus={EWorkflowsLoadingStatus.Loaded}
        />
      </IntlProvider>,
    );

    expect(hookResult.shouldSkeletonOptionalTable).toBe(false);
    expect(hookResult.columns.some((column) => column.accessor === 'new-field')).toBe(true);
  });
});
