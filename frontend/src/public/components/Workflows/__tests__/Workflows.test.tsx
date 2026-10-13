import React from 'react';
import { act, render } from '@testing-library/react';
import { createMemoryHistory } from 'history';
import { useDispatch, useSelector } from 'react-redux';
import { Route, Router, Switch } from 'react-router-dom';

import { ERoutes } from '../../../constants/routes';
import { EWorkflowsView } from '../../../types/workflow';
import { Workflows } from '../Workflows';

jest.mock('react-redux', () => ({
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

jest.mock('../WorkflowsGridPage', () => ({
  __esModule: true,
  default: () => <div>Grid view</div>,
}));

jest.mock('../WorkflowsTablePage', () => ({
  __esModule: true,
  default: () => <div>Table view</div>,
}));

describe('Workflows routing', () => {
  it('does not remount workflows when replacing the list route with a detail route', () => {
    const dispatch = jest.fn();
    const memoryHistory = createMemoryHistory({ initialEntries: [ERoutes.Workflows] });
    (useDispatch as jest.Mock).mockReturnValue(dispatch);
    (useSelector as jest.Mock).mockReturnValue(EWorkflowsView.Table);

    render(
      <Router history={memoryHistory}>
        <Switch>
          <Route path={ERoutes.WorkflowDetail} component={Workflows} />
          <Route path={ERoutes.Workflows} component={Workflows} />
        </Switch>
      </Router>,
    );

    act(() => memoryHistory.replace(ERoutes.WorkflowDetail.replace(':id', '42')));

    expect(dispatch).not.toHaveBeenCalled();
  });
});
