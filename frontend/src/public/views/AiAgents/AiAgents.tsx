import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { Loader } from '../../components/UI';
import { TopNavContainer } from '../../components/TopNav';

const AiAgents = loadable(
  () => import(/* webpackChunkName: "aiAgents", webpackPrefetch: true */ '../../components/AiAgents'),
  { fallback: <Loader isLoading /> },
);

export const AiAgentsView = () => {
  return (
    <>
      <TopNavContainer />
      <main>
        <div className="container-fluid">
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
        </div>
      </main>
    </>
  );
};
