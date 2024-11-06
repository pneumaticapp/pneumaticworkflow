import * as React from 'react';
import { Route, Switch, Redirect, RouteComponentProps } from 'react-router-dom';
import loadable from '@loadable/component';

import { ERoutes } from '../../constants/routes';
import { SettingsLayout } from '../../layout';
import { Loader } from '../../components/UI';

const AccountSettings = loadable(
  () => import(/* webpackChunkName: "account_settings", webpackPrefetch: true */ '../../components/ProfileAccount'),
  { fallback: <Loader isLoading /> },
);
const UserProfile = loadable(
  () => import(/* webpackChunkName: "user_profile", webpackPrefetch: true */ '../../components/Profile'),
  { fallback: <Loader isLoading /> },
);

export const Settings = ({ match }: RouteComponentProps) => {
  return (
    <SettingsLayout>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Redirect exact from={`${match.url}/`} to={ERoutes.Login} />
          <Route path={ERoutes.AccountSettings} component={AccountSettings} />
          <Route path={ERoutes.Profile} component={UserProfile} />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </SettingsLayout>
  );
};
