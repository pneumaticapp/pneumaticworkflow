import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { Loader } from '../../components/UI';
import { TemplatesLayout } from '../../layout';

const Datasets = loadable(
  () => import(/* webpackChunkName: "datasets", webpackPrefetch: true */ '../../components/Datasets'),
  { fallback: <Loader isLoading /> },
);

export const DatasetsView = () => {
  return (
    <TemplatesLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.Datasets}
            component={Datasets}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TemplatesLayout>
  );
};
