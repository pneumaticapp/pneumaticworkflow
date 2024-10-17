/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { INotificationsListProps, NotificationsList } from './NotificationsList';
import { IApplicationState } from '../../types/redux';
import {
  setNotificationsListIsOpen,
  removeNotificationItem,
  fetchNotificationsAsRead,
  markNotificationsAsRead,
  changeNotificationsList,
  loadNotificationsList,
} from '../../redux/actions';
import { getPaywallType } from '../TopNav/utils/getPaywallType';

type TStoreProps = Pick<
  INotificationsListProps,
  'notifications' | 'isLoading' | 'withPaywall' | 'users' | 'totalNotificationsCount'
>;
type TDispatchProps = Pick<
  INotificationsListProps,
  | 'setNotificationsListIsOpen'
  | 'removeNotificationItem'
  | 'fetchNotificationsAsRead'
  | 'markNotificationsAsRead'
  | 'changeNotificationsList'
  | 'loadNotificationsList'
>;

export function mapStateToProps({
  notifications: { items: notifications, isLoading, totalItemsCount: totalNotificationsCount },
  accounts: { users },
  authUser: {
    account: { billingPlan, isBlocked },
  },
}: IApplicationState): TStoreProps {
  const withPaywall = Boolean(getPaywallType(billingPlan, isBlocked));

  return { notifications, isLoading, withPaywall, users, totalNotificationsCount };
}

export const mapDispatchToProps: TDispatchProps = {
  setNotificationsListIsOpen,
  removeNotificationItem,
  fetchNotificationsAsRead,
  markNotificationsAsRead,
  changeNotificationsList,
  loadNotificationsList,
};

export const NotificationsListContainer = connect<TStoreProps, TDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(NotificationsList);
