import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { TenantsLayout } from '../../layout';
import { Loader } from '../../components/UI';

const Tenants = loadable(
  () => import(/* webpackChunkName: "tenants", webpackPrefetch: true */ '../../components/Tenants'),
  { fallback: <Loader isLoading /> },
);

export const TenantsView = () => {
  return (
    <TenantsLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.Tenants}
            component={Tenants}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TenantsLayout>
  );
};
