import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import WorkflowsGridPage from './WorkflowsGridPage';
import WorkflowsTablePage from './WorkflowsTablePage';

import { getWorkflowsView } from '../../redux/selectors/workflows';
import { EWorkflowsView } from '../../types/workflow';
import { TITLES } from '../../constants/titles';
import { resetWorkflows, openWorkflowLogPopup } from '../../redux/actions';

export interface IWorkflowsLocationMatchParams {
  id?: string;
};

export const Workflows = withRouter(({ match: { params } }: RouteComponentProps<IWorkflowsLocationMatchParams>) => {
  const view = useSelector(getWorkflowsView);
  const dispatch = useDispatch();

  const clearWorkflowsList = () => {
    dispatch(resetWorkflows());
  }

  React.useEffect(() => {
    document.title = TITLES.Workflows;

    const workflowId = Number(params.id);
    if (workflowId) {
      dispatch(openWorkflowLogPopup({ workflowId, redirectTo404IfNotFound: true }));
    }

    return clearWorkflowsList;
  }, []);

  const pageMap = {
    [EWorkflowsView.Table]: <WorkflowsTablePage />,
    [EWorkflowsView.Grid]: <WorkflowsGridPage />,
  }

  return pageMap[view];
})
