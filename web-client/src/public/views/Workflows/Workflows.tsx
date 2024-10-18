import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { WorkflowsLayout } from '../../layout';
import { Loader } from '../../components/UI';

const Workflows = loadable(
  () => import(/* webpackChunkName: "workflows_grid", webpackPrefetch: true */ '../../components/Workflows'),
  { fallback: <Loader isLoading /> },
);

export const WorkflowsView = () => {
  return (
    <WorkflowsLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route path={ERoutes.WorkflowDetail} component={Workflows} />
          <Route path={ERoutes.Workflows} component={Workflows} />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </WorkflowsLayout>
  );
};
