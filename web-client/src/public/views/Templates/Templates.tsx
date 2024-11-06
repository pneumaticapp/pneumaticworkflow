import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { TemplatesLayout } from '../../layout';
import { Loader } from '../../components/UI';

const Templates = loadable(
  () => import(/* webpackChunkName: "templates", webpackPrefetch: true */ '../../components/Templates'),
  { fallback: <Loader isLoading /> },
);

export const TemplatesView = () => {
  return (
    <TemplatesLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.Templates}
            component={Templates}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TemplatesLayout>
  );
};
