import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { useDocumentTitle } from '../../hooks/useDocumentTitle';
import { ERoutes } from '../../constants/routes';
import { IntegrationsLayout } from '../../layout';
import { Loader } from '../../components/UI';

const Integrations = loadable(
  () => import(/* webpackChunkName: "integrations", webpackPrefetch: true */ '../../components/IntegrationsList'),
  { fallback: <Loader isLoading /> },
);

export const IntegrationsView = () => {
  useDocumentTitle('Integrations');

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
