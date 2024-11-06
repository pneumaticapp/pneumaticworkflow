import React from 'react';
import classnames from 'classnames';
import { UnregisterCallback } from 'history';

import { SelectTemplateModalContainer } from '../../components/SelectTemplateModal';
import { NotificationsListContainer } from '../../components/NotificationsList/container';
import { WorkflowEditPopupContainer } from '../../components/WorkflowEditPopup';
import { GeneralLoader } from '../../components/GeneralLoader';
import { SidebarContainer } from '../../components/Sidebar';
import { ILoadNotificationsPayload } from '../../redux/notifications/actions';
import { useDelayUnmount } from '../../hooks/useDelayUnmount';
import { TeamInvitesPopupContainer } from '../../components/TeamInvitesPopup';
import { checkSomeRouteIsActive, history } from '../../utils/history';
import { initFirebaseMessaging } from '../../firebase';
import { IAuthUser } from '../../types/redux';
import { identifyUser } from '../../utils/analytics';
import { setIntercomUser } from '../../utils/setIntercomUser';
import { TemplateAIModalContainer } from '../../components/TemplateAIModal';
import { ESubscriptionPlan } from '../../types/account';

import { ERoutes } from '../../constants/routes';
import { EPlanActions } from '../../utils/getPlanPendingActions';
import { Paywall } from '../../components/UI/Paywall';

import styles from './MainLayout.css';
import { IUnsavedUser, TUserListItem } from '../../types/user';

import { isEnvAnalytics, isEnvPush } from '../../constants/enviroment';

export interface IMainLayoutComponentStoreProps {
  user: IAuthUser;
  isNotificationsListOpen: boolean;
  isRunWorkflowModalOpen: boolean;
  isGeneralLoaderVisible: boolean;
  users: TUserListItem[];
  pendingActions: EPlanActions[];
  loadNotificationsList(payload?: ILoadNotificationsPayload): void;
  authenticateUser(): void;
  watchUserWSEventsAction(): void;
  loadTasksCount(): void;
  loadUsers(): void;
  loadTenantsCount(): void;
  loadActiveUsersCount(): void;
  generateMenu(): void;
  loadPlan(): void;
}

const EXPIRED_TRIAL_PERMITTED_ROUTES = [
  ERoutes.Root,
  ERoutes.CollectPaymentDetails,
  ERoutes.AfterPaymentDetailsProvided,
  ERoutes.Error,
  ERoutes.Login,
  ERoutes.SuperuserLogin,
  ERoutes.Register,
  ERoutes.SignUpGoogle,
  ERoutes.SignUpInvite,
  ERoutes.ForgotPassword,
  ERoutes.ResetPassword,
];

export interface IMainLayoutComponentOwnProps {
  classNames: string;
  children?: React.ReactNode;
}

export type IMainLayoutComponentProps = IMainLayoutComponentStoreProps & IMainLayoutComponentOwnProps;

export function MainLayout({
  children,
  classNames,
  isNotificationsListOpen,
  isRunWorkflowModalOpen,
  isGeneralLoaderVisible,
  user,
  users,
  pendingActions,
  loadNotificationsList,
  watchUserWSEventsAction,
  loadTasksCount,
  loadUsers,
  loadActiveUsersCount,
  loadTenantsCount,
  generateMenu,
  loadPlan,
}: IMainLayoutComponentProps) {
  const unregisterHistoryListener = React.useRef<UnregisterCallback | null>(null);
  const [prevLocation, setPrevLocation] = React.useState<string | null>(null);

  const accountOwner = users.filter((localUser) => localUser.isAccountOwner)[0] as IUnsavedUser;
  const isPlanExpired =
    pendingActions.includes(EPlanActions.ChoosePlan) &&
    !checkSomeRouteIsActive(...EXPIRED_TRIAL_PERMITTED_ROUTES);

  React.useEffect(() => {
    if (user.account.paymentCardProvided) {
      loadNotificationsList();
      watchUserWSEventsAction();
      loadTasksCount();
      loadUsers();
      loadActiveUsersCount();
      generateMenu();
      loadPlan();

      if (isEnvPush) initFirebaseMessaging();

      if (
        user.isAdmin &&
        user.account.leaseLevel !== 'tenant' &&
        user.account.billingPlan !== ESubscriptionPlan.Free &&
        user.account.isSubscribed
      ) {
        loadTenantsCount();
      }
    }
  }, [user.id, user.account.paymentCardProvided]);

  React.useLayoutEffect(() => {
    if (!user.isSupermode) {
      identifyUser(user);

      if (isEnvAnalytics) {
        setIntercomUser(user);
      }
    }
  }, [user.id, user.isSupermode]);

  React.useEffect(() => {
    if (!user.account.paymentCardProvided) {
      return undefined;
    }

    unregisterHistoryListener.current = history.listen((listener) => {
      const newLocation = listener.pathname;
      if (newLocation !== prevLocation) {
        loadTasksCount();
        loadActiveUsersCount();
      }

      setPrevLocation(newLocation);
    });

    return () => {
      unregisterHistoryListener.current?.();
    };
  }, [user.account.paymentCardProvided]);

  const shouldRenderNotifications = useDelayUnmount(isNotificationsListOpen, 150);

  return (
    <>
      <div id="app-container" className={classnames(classNames, styles['main-layout'])}>
        {children}
        <SidebarContainer />
      </div>
      {isPlanExpired && <Paywall currentUser={user} owner={accountOwner} />}
      {isGeneralLoaderVisible && <GeneralLoader />}
      {shouldRenderNotifications && <NotificationsListContainer isClosing={!isNotificationsListOpen} />}
      {isRunWorkflowModalOpen && <WorkflowEditPopupContainer />}

      <SelectTemplateModalContainer />
      <TemplateAIModalContainer />
      <TeamInvitesPopupContainer />
    </>
  );
}
