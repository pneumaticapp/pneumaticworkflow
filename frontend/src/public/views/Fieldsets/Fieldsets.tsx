import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { Loader } from '../../components/UI';
import { TemplatesLayout } from '../../layout';

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
    <TemplatesLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.FieldsetDetail}
            component={FieldsetDetails}
          />
          <Route
            exact
            path={ERoutes.Fieldsets}
            component={Fieldsets}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TemplatesLayout>
  );
};
