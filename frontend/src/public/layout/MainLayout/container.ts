import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import {
  loadNotificationsList,
  authenticateUser,
  watchUserWSEventsAction,
  loadTasksCount,
  usersFetchStarted,
  loadActiveUsersCount,
  generateMenu,
  loadPlan,
  loadTenantsCount,
} from '../../redux/actions';

import { IMainLayoutComponentStoreProps, MainLayout } from './MainLayout';
import { getUserPendingActions } from '../../redux/selectors/user';

export type TMainLayoutComponentStoreProps = Pick<
  IMainLayoutComponentStoreProps,
  'isRunWorkflowModalOpen' | 'isNotificationsListOpen' | 'pendingActions' | 'isGeneralLoaderVisible' | 'user' | 'users'
>;

export type TMainLayoutComponentDispatchProps = Pick<
  IMainLayoutComponentStoreProps,
  | 'loadNotificationsList'
  | 'authenticateUser'
  | 'watchUserWSEventsAction'
  | 'loadTasksCount'
  | 'loadUsers'
  | 'loadTenantsCount'
  | 'generateMenu'
  | 'loadActiveUsersCount'
  | 'loadPlan'
>;

const mapStateToProps = (state: IApplicationState): TMainLayoutComponentStoreProps => {
  const {
    runWorkflowModal,
    notifications,
    general: { isLoaderVisible: isGeneralLoaderVisible },
    authUser,
    accounts: { users }
  } = state;
  const { isOpen: isRunWorkflowModalOpen } = runWorkflowModal;
  const { isNotificationsListOpen } = notifications;
  const pendingActions = getUserPendingActions(state);

  return {
    isRunWorkflowModalOpen,
    isNotificationsListOpen,
    isGeneralLoaderVisible,
    user: authUser,
    pendingActions,
    users
  };
};

const mapDispatchToProps: TMainLayoutComponentDispatchProps = {
  loadNotificationsList,
  authenticateUser,
  watchUserWSEventsAction,
  generateMenu,
  loadTasksCount,
  loadUsers: usersFetchStarted,
  loadActiveUsersCount,
  loadTenantsCount,
  loadPlan,
};

export const MainLayoutContainer = connect(mapStateToProps, mapDispatchToProps)(MainLayout);
