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

const DatasetDetails = loadable(
  () => import(/* webpackChunkName: "datasetDetails", webpackPrefetch: true */ '../../components/Datasets/DatasetDetails'),
  { fallback: <Loader isLoading /> },
);

export const DatasetsView = () => {
  return (
    <TemplatesLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.DatasetDetail}
            component={DatasetDetails}
          />
          <Route
            exact
            path={ERoutes.Datasets}
            component={Datasets}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TemplatesLayout>
  );
};
