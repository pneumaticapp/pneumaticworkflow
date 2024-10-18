/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { HighlightsLayout } from '../../layout';
import { Loader } from '../../components/UI';

const Highlights = loadable(
  () => import(/* webpackChunkName: "highlights", webpackPrefetch: true */ '../../components/Highlights'),
  { fallback: <Loader isLoading /> },
);

export const HighlightsView = () => {
  return (
    <HighlightsLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            path={ERoutes.Highlights}
            component={Highlights}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </HighlightsLayout>
  );
};
