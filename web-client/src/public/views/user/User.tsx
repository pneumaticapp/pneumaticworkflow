import * as React from 'react';
import { Route, Switch, Redirect, RouteComponentProps } from 'react-router-dom';

import { ERoutes } from '../../constants/routes';
import { ExpiredInvite } from './ExpiredInvite/ExpiredInvite';
import { ForgotPasswordContainer } from './ForgotPassword';
import { LoginContainer } from './Login';
import { RegisterContainer } from './Register';
import { RegisterInviteContainer } from './RegisterInvite';
import { ResetPasswordContainer } from './ResetPassword';
import { SuperuserLoginContainer } from './SuperuserLogin';
import { UserLayoutContainer } from '../../layout/UserLayout/container';
import { RegisterGoogleContainer } from './RegisterGoogle'
import { isEnvSignup } from '../../constants/enviroment';

export const User = ({ match }: RouteComponentProps) => {
  return (
    <UserLayoutContainer>
      <React.Suspense fallback={<div className="loading" />}>
        <Switch>
          <Route path={ERoutes.ForgotPassword} component={ForgotPasswordContainer} />
          <Route path={ERoutes.ExpiredInvite} component={ExpiredInvite} />
          <Route path={ERoutes.ResetPassword} component={ResetPasswordContainer} />
          <Redirect exact from={`${match.url}/`} to={ERoutes.Login} />
          <Route path={ERoutes.Login} component={LoginContainer} />
          <Route path={ERoutes.SignUpInvite} component={RegisterInviteContainer} />
          <Route path={ERoutes.SignUpGoogle} component={RegisterGoogleContainer} />
          {isEnvSignup && <Route path={ERoutes.Register} component={RegisterContainer} />}
          <Route path={ERoutes.SuperuserLogin} component={SuperuserLoginContainer} />
          <Redirect to={ERoutes.Error} />
        </Switch>
      </React.Suspense>
    </UserLayoutContainer>
  );
};
