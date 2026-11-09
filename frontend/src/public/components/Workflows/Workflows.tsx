import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import WorkflowsGridPage from './WorkflowsGridPage';
import WorkflowsTablePage from './WorkflowsTablePage';

import { getWorkflowsView } from '../../redux/selectors/workflows';
import { EWorkflowsView } from '../../types/workflow';
import { IApplicationState } from '../../types/redux';
import { useDocumentTitle } from '../../hooks/useDocumentTitle';
import { openWorkflowLogPopup, resetWorkflows } from '../../redux/workflows/slice';

export interface IWorkflowsLocationMatchParams {
  id?: string;
}

export const Workflows = withRouter(({ match: { params } }: RouteComponentProps<IWorkflowsLocationMatchParams>) => {
  const view = useSelector(getWorkflowsView);
  const workflow = useSelector((state: IApplicationState) => state.workflows.workflow);
  useDocumentTitle('Workflows', params.id && workflow?.id === Number(params.id) ? workflow.name : undefined);
  const dispatch = useDispatch();

  const clearWorkflowsList = () => {
    dispatch(resetWorkflows());
  };

  React.useEffect(() => {
    const workflowId = Number(params.id);
    if (workflowId) {
      dispatch(openWorkflowLogPopup({ workflowId, redirectTo404IfNotFound: true }));
    }

    return clearWorkflowsList;
  }, []);

  const pageMap = {
    [EWorkflowsView.Table]: <WorkflowsTablePage />,
    [EWorkflowsView.Grid]: <WorkflowsGridPage />,
  };

  return pageMap[view];
});
