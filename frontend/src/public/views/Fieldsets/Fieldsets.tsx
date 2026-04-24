import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { Loader } from '../../components/UI';

const Fieldsets = loadable(
  () => import(/* webpackChunkName: "fieldsets", webpackPrefetch: true */ '../../components/Fieldsets'),
  { fallback: <Loader isLoading /> },
);

const FieldsetDetails = loadable(
  () => import(/* webpackChunkName: "fieldsetDetails", webpackPrefetch: true */ '../../components/Fieldsets/FieldsetDetails'),
  { fallback: <Loader isLoading /> },
);

export const FieldsetsView = () => {
  return (
    <React.Suspense fallback={<div className="loading" />}>
      <Switch>
        <Route
          path={ERoutes.TemplateFieldsetDetail}
          component={FieldsetDetails}
        />
        <Route
          exact
          path={ERoutes.TemplateFieldsets}
          component={Fieldsets}
        />
        <Redirect to={ERoutes.Error} />
      </Switch>
    </React.Suspense>
  );
};
