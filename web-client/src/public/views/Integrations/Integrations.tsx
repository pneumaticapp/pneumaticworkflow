import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { TITLES } from '../../constants/titles';
import { ERoutes } from '../../constants/routes';
import { IntegrationsLayout } from '../../layout';
import { Loader } from '../../components/UI';

const Integrations = loadable(
  () => import(/* webpackChunkName: "integrations", webpackPrefetch: true */ '../../components/IntegrationsList'),
  { fallback: <Loader isLoading /> },
);

export const IntegrationsView = () => {
  React.useEffect(() => {
    document.title = TITLES.Integrations;
  }, []);

  return (
    <IntegrationsLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route path={ERoutes.Integrations} component={Integrations} />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </IntegrationsLayout>
  );
};
