import * as React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';

import { checkSomeRouteIsActive } from '../../utils/history';
import { REDIRECT_URL_STORAGE_KEY } from '../../constants/storageKeys';
import { ERoutes } from '../../constants/routes';
import { Error } from '../../views/Error';
import { Main } from '../../views/Main';
import { WorkflowsView } from '../../views/Workflows';
import { HighlightsView } from '../../views/Highlights';
import { ProtectedRoute } from '../ProtectedRoute';
import { Settings } from '../../views/Settings';
import { TasksView } from '../../views/Tasks';
import { TeamView } from '../../views/Team';
import { User } from '../../views/user';
import { TemplatesView } from '../../views/Templates';
import { TemplateView } from '../../views/Template';
import { IntegrationsView } from '../../views/Integrations';
import { IntegrationDetailsView } from '../../views/IntegrationDetails';
import { MainLayout } from '../../layout';
import { GuestTask } from '../GuestTask';
import { TenantsView } from '../../views/Tenants';
import { ELoggedState, IAuthUser } from '../../types/redux';
import { CollectPaymentDetails } from '../CollectPaymentDetails';
import { AfterPaymentDetailsProvided } from '../AfterPaymentDetailsProvided';
import { ESubscriptionPlan } from '../../types/account';

export interface IAppRoutesProps {
  user: IAuthUser;
  containerClassnames: string;
}

const REDIRECT_FORBIDDEN_ROUTES = [
  ERoutes.Root,
  ERoutes.Login,
  ERoutes.SuperuserLogin,
  ERoutes.Register,
  ERoutes.SignUpGoogle,
  ERoutes.SignUpInvite,
  ERoutes.ForgotPassword,
  ERoutes.ResetPassword,
  ERoutes.CollectPaymentDetails,
  ERoutes.AfterPaymentDetailsProvided,
];

export function AppRoutes({ containerClassnames, user }: IAppRoutesProps) {
  const redirectUrl = sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY);

  const shouldRedirectToUrl = redirectUrl && !checkSomeRouteIsActive(...REDIRECT_FORBIDDEN_ROUTES);

  if (shouldRedirectToUrl) {
    sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, '');

    return <Redirect to={redirectUrl!} />;
  }

  return (
    <Switch>
      <Route path={ERoutes.Error} exact component={Error} />
      <Route path="/auth/" component={User} />

      <Route path={ERoutes.GuestTask} component={GuestTask} />

      <ProtectedRoute hasAccessAuth={user.loggedState !== ELoggedState.LoggedOut}>
        <MainLayout classNames={containerClassnames}>
          <Switch>
            <Route exact path={ERoutes.Main} component={Main} />
            <Route path={ERoutes.CollectPaymentDetails} component={CollectPaymentDetails} />
            <Route path={ERoutes.AfterPaymentDetailsProvided} component={AfterPaymentDetailsProvided} />
            <Route path={ERoutes.Settings} component={Settings} />
            <ProtectedRoute path={ERoutes.Workflows} hasAccess={Boolean(user.isAdmin)}>
              <WorkflowsView />
            </ProtectedRoute>
            <ProtectedRoute path={ERoutes.WorkflowDetail} hasAccess={Boolean(user.isAdmin)}>
              <WorkflowsView />
            </ProtectedRoute>
            <ProtectedRoute path={ERoutes.TemplatesCreate} hasAccess={Boolean(user.isAdmin)}>
              <TemplateView />
            </ProtectedRoute>
            <ProtectedRoute path={ERoutes.TemplateView} hasAccess={Boolean(user.isAdmin)}>
              <TemplateView />
            </ProtectedRoute>
            <ProtectedRoute path={ERoutes.TemplatesEdit} hasAccess={Boolean(user.isAdmin)}>
              <TemplateView />
            </ProtectedRoute>
            <ProtectedRoute path={ERoutes.Templates} hasAccess={Boolean(user.isAdmin)}>
              <TemplatesView />
            </ProtectedRoute>
            <Route path={ERoutes.Tasks} component={TasksView} />
            <ProtectedRoute path={ERoutes.Highlights} hasAccess={Boolean(user.isAdmin)}>
              <HighlightsView />
            </ProtectedRoute>
            <ProtectedRoute path={ERoutes.Team} hasAccess={Boolean(user.isAdmin)}>
              <TeamView />
            </ProtectedRoute>
            <ProtectedRoute path={ERoutes.IntegrationsDetail} hasAccess={Boolean(user.isAdmin)}>
              <IntegrationDetailsView />
            </ProtectedRoute>
            <ProtectedRoute exact path={ERoutes.Integrations} hasAccess={Boolean(user.isAdmin)}>
              <IntegrationsView />
            </ProtectedRoute>
            <ProtectedRoute
              exact
              path={ERoutes.Tenants}
              hasAccess={Boolean(
                user.isAdmin &&
                  user.account.billingPlan !== ESubscriptionPlan.Free &&
                  user.account.leaseLevel !== 'tenant',
              )}
            >
              <TenantsView />
            </ProtectedRoute>

            <Redirect exact from="/" to={ERoutes.Main} />
            <Redirect to={ERoutes.Error} />
          </Switch>
        </MainLayout>
      </ProtectedRoute>
    </Switch>
  );
}
