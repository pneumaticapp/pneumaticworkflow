import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { Loader } from '../../components/UI';
import { TemplatesLayout } from '../../layout';

const AiAgents = loadable(
  () => import(/* webpackChunkName: "aiAgents", webpackPrefetch: true */ '../../components/AiAgents'),
  { fallback: <Loader isLoading /> },
);

export const AiAgentsView = () => {
  return (
    <TemplatesLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route
            exact
            path={ERoutes.AiAgents}
            component={AiAgents}
          />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TemplatesLayout>
  );
};
