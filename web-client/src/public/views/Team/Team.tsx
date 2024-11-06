import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { TeamLayout } from '../../layout';
import { ERoutes } from '../../constants/routes';
import { Loader } from '../../components/UI';

const Team = loadable(
  () => import(/* webpackChunkName: "team", webpackPrefetch: true */ '../../components/Team'),
  { fallback: <Loader isLoading /> },
);

export const TeamView = () => {
  return (
    <TeamLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.Team}
            component={Team}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TeamLayout>
  );
};
