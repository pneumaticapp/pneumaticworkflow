import React from 'react';
import classnames from 'classnames';
import { UnregisterCallback } from 'history';
import { useSelector, useDispatch } from 'react-redux';

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
import { TuneViewModal } from '../../components/TuneViewModal';

import { ERoutes } from '../../constants/routes';
import { EPlanActions } from '../../utils/getPlanPendingActions';
import { Paywall } from '../../components/UI/Paywall';
import { isEnvAnalytics, isEnvPush } from '../../constants/enviroment';
import { IUnsavedUser, TUserListItem } from '../../types/user';
import { checkIsTemplateOwner, loadGroups } from '../../redux/actions';
import { getIsAdmin } from '../../redux/selectors/user';
import { closeAllConnections, hasActiveConnections } from '../../redux/utils/webSocketConnections';
import { promiseDelay } from '../../utils/timeouts';

import styles from './MainLayout.css';

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
  const dispatch = useDispatch();
  const unregisterHistoryListener = React.useRef<UnregisterCallback | null>(null);
  const prevLocationRef = React.useRef<string | null>(null);

  const accountOwner = users.filter((localUser) => localUser.isAccountOwner)[0] as IUnsavedUser;
  const isPlanExpired =
    pendingActions.includes(EPlanActions.ChoosePlan) && !checkSomeRouteIsActive(...EXPIRED_TRIAL_PERMITTED_ROUTES);
  const { isSubscribed, billingPlan } = user.account;

  const isAdmin = useSelector(getIsAdmin);

  React.useEffect(() => {
    if (billingPlan) {
      if (hasActiveConnections()) {
        closeAllConnections()
          .then(() => promiseDelay(500))
          .then(() => watchUserWSEventsAction());
      } else {
        watchUserWSEventsAction();
      }

      loadNotificationsList();
      loadTasksCount();
      loadUsers();
      loadActiveUsersCount();
      generateMenu();
      loadPlan();
      dispatch(loadGroups());

      if (isEnvPush) initFirebaseMessaging();

      if (
        user.isAdmin &&
        user.account.leaseLevel !== 'tenant' &&
        (user.account.isSubscribed || billingPlan === ESubscriptionPlan.Free)
      ) {
        loadTenantsCount();
      }
    }
  }, [user.id, billingPlan]);

  React.useLayoutEffect(() => {
    if (!user.isSupermode) {
      identifyUser(user);

      if (isEnvAnalytics) {
        setIntercomUser(user);
      }
    }
  }, [user.id, user.isSupermode]);

  React.useEffect(() => {
    if (!isSubscribed && !(billingPlan === ESubscriptionPlan.Free)) {
      return undefined;
    }
    unregisterHistoryListener.current = history.listen((listener) => {
      const newLocation = listener.pathname;
      if (newLocation !== prevLocationRef.current) {
        loadTasksCount();
        loadActiveUsersCount();
      }

      prevLocationRef.current = newLocation;
    });

    return () => {
      unregisterHistoryListener.current?.();
    };
  }, [isSubscribed, billingPlan, loadTasksCount, loadActiveUsersCount]);

  React.useEffect(() => {
    if (!isAdmin) {
      dispatch(checkIsTemplateOwner());
    }
  }, [dispatch, isAdmin]);

  const shouldRenderNotifications = useDelayUnmount(isNotificationsListOpen, 150);

  return (
    <>
      <div id="app-container" className={classnames(classNames, styles['main-layout'])}>
        {children}
        <SidebarContainer />
      </div>
      {((!isSubscribed && !(billingPlan === ESubscriptionPlan.Free)) || isPlanExpired) && (
        <Paywall currentUser={user} owner={accountOwner} />
      )}

      {isGeneralLoaderVisible && <GeneralLoader />}
      {shouldRenderNotifications && <NotificationsListContainer isClosing={!isNotificationsListOpen} />}
      {isRunWorkflowModalOpen && <WorkflowEditPopupContainer />}

      <SelectTemplateModalContainer />
      <TemplateAIModalContainer />
      <TeamInvitesPopupContainer />
      <TuneViewModal />
    </>
  );
}
