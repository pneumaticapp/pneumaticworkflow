/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { TemplateLayout } from '../../layout';
import { Loader } from '../../components/UI';

const Template = loadable(
  () => import(/* webpackChunkName: "template", webpackPrefetch: true */ '../../components/TemplateEdit'),
  { fallback: <Loader isLoading /> },
);

export const TemplateView = () => {
  return (
    <TemplateLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.TemplateView}
            component={Template}
            exact={true}
          />
          <Route
            path={ERoutes.TemplatesCreate}
            component={Template}
          />
          <Route
            path={ERoutes.TemplatesEdit}
            component={Template}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TemplateLayout>
  );
};
