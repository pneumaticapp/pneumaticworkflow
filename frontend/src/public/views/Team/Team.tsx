import * as React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { Loader } from '../../components/UI';
import { TeamLayout } from '../../layout';

const Users = loadable(
  () => import(/* webpackChunkName: "team", webpackPrefetch: true */ '../../components/Team/Users'),
  {
    fallback: <Loader isLoading />,
  },
);

const Groups = loadable(
  () => import(/* webpackChunkName: "groups", webpackPrefetch: true */ '../../components/Team/Groups'),
  {
    fallback: <Loader isLoading />,
  },
);

const GroupDetails = loadable(
  () => import(/* webpackChunkName: "groupDetails", webpackPrefetch: true */ '../../components/Team/GroupDetails'),
  {
    fallback: <Loader isLoading />,
  },
);

export const TeamView = () => {
  return (
    <TeamLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route path={ERoutes.GroupDetails} component={GroupDetails} />
          <Route path={ERoutes.Groups} component={Groups} />
          <Route path={ERoutes.Team} component={Users} />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </TeamLayout>
  );
};
