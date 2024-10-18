/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { IntegrationDetailsLayout } from '../../layout';
import { ERoutes } from '../../constants/routes';
import { Loader } from '../../components/UI';

const Integration = loadable(
  () => import(/* webpackChunkName: "integration", webpackPrefetch: true */ '../../components/IntegrationDetails'),
  { fallback: <Loader isLoading /> },
);

export const IntegrationDetailsView = () => {
  return (
    <IntegrationDetailsLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.IntegrationsDetail}
            component={Integration}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </IntegrationDetailsLayout>
  );
};
