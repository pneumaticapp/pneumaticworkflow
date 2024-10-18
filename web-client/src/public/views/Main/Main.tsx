/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { DashboardLayout } from '../../layout';
import { ERoutes } from '../../constants/routes';
import { TITLES } from '../../constants/titles';
import { Loader } from '../../components/UI';

const Dashboard = loadable(
  () => import(/* webpackChunkName: "dashboard", webpackPrefetch: true */ '../../components/Dashboard'),
  { fallback: <Loader isLoading /> },
);

export const Main = () => {
  React.useEffect(() => {
    document.title = TITLES.Main;
  }, []);

  return (
    <DashboardLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.Main}
            component={Dashboard}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </DashboardLayout>
  );
};
