/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-line-length
import { ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { TNotificationsListItem } from '../../types';

export const enum ENotificationsActions {
  LoadList = 'LOAD_NOTIFICATIONS_LIST',
  LoadListFailed = 'LOAD_NOTIFICATIONS_LIST_FAILED',
  ChangeList = 'CHANGE_NOTIFICATIONS_LIST',
  ChangeUnreadCount = 'CHANGE_UNREAD_NOTIFICATIONS_COUNT',
  SetIsOpen = 'SET_NOTIFICATIONS_LIST_IS_OPEN',
  RemoveNotificationItem = 'REMOVE_NOTIFICATION_ITEM',
  ChangeHasNew = 'CHANGE_HAS_NEW_NOTIFICATIONS',
  FetchNotificationsAsRead = 'FETCH_NOTIFICATIONS_AS_READ',
  MarkNotificationsAsRead = 'MARK_NOTIFICATIONS_AS_READ',
}

export interface ILoadNotificationsPayload {
  offset: number;
}

export type TLoadNotifications = ITypedReduxAction<ENotificationsActions.LoadList, ILoadNotificationsPayload | undefined>;
export const loadNotificationsList: (payload?: ILoadNotificationsPayload | undefined) => TLoadNotifications =
  actionGenerator<ENotificationsActions.LoadList, ILoadNotificationsPayload | undefined>(ENotificationsActions.LoadList);

export interface IChangeNotificationsListPayload {
  items: TNotificationsListItem[];
  count?: number;
}
export type TChangeNotificationsList = ITypedReduxAction<ENotificationsActions.ChangeList, IChangeNotificationsListPayload>;
export const changeNotificationsList: (payload: IChangeNotificationsListPayload) => TChangeNotificationsList =
  actionGenerator<ENotificationsActions.ChangeList, IChangeNotificationsListPayload>(ENotificationsActions.ChangeList);

export type TLoadNotificationsListFailed = ITypedReduxAction<ENotificationsActions.LoadListFailed, void>;
export const loadNotificationsListFailed: (payload?: void) => TLoadNotificationsListFailed =
  actionGenerator<ENotificationsActions.LoadListFailed, void>(ENotificationsActions.LoadListFailed);

export type TSetNotificationsListIsOpen = ITypedReduxAction<ENotificationsActions.SetIsOpen, boolean>;
export const setNotificationsListIsOpen: (payload: boolean) => TSetNotificationsListIsOpen =
  actionGenerator<ENotificationsActions.SetIsOpen, boolean>(ENotificationsActions.SetIsOpen);

export type TRemoveNotificationPayload = { notificationId: number };
export type TRemoveNotificationItem = ITypedReduxAction<
ENotificationsActions.RemoveNotificationItem,
TRemoveNotificationPayload>;
export const removeNotificationItem: (payload: TRemoveNotificationPayload) => TRemoveNotificationItem =
  actionGenerator<ENotificationsActions.RemoveNotificationItem, TRemoveNotificationPayload>(
    ENotificationsActions.RemoveNotificationItem,
  );

export type TChangeHasNewNotifications = ITypedReduxAction<ENotificationsActions.ChangeHasNew, boolean>;
export const changeHasNewNotifications: (payload: boolean) => TChangeHasNewNotifications =
  actionGenerator<ENotificationsActions.ChangeHasNew, boolean>(ENotificationsActions.ChangeHasNew);

export type TFetchNotificationsAsRead = ITypedReduxAction<ENotificationsActions.FetchNotificationsAsRead, void>;
export const fetchNotificationsAsRead: (payload?: void) => TFetchNotificationsAsRead =
  actionGenerator<ENotificationsActions.FetchNotificationsAsRead, void>(ENotificationsActions.FetchNotificationsAsRead);

export type TMarkNotificationsAsRead = ITypedReduxAction<ENotificationsActions.MarkNotificationsAsRead, void>;
export const markNotificationsAsRead: (payload?: void) => TMarkNotificationsAsRead =
  actionGenerator<ENotificationsActions.MarkNotificationsAsRead, void>(ENotificationsActions.MarkNotificationsAsRead);

export type TChangeUnreadNotificationsCount = ITypedReduxAction<ENotificationsActions.ChangeUnreadCount, number>;
export const changeUnreadNotificationsCount: (payload: number) => TChangeUnreadNotificationsCount =
  actionGenerator<ENotificationsActions.ChangeUnreadCount, number>(ENotificationsActions.ChangeUnreadCount);

export type TNotificationsActions =
  TLoadNotifications
  | TChangeNotificationsList
  | TLoadNotificationsListFailed
  | TSetNotificationsListIsOpen
  | TRemoveNotificationItem
  | TChangeHasNewNotifications
  | TFetchNotificationsAsRead
  | TMarkNotificationsAsRead
  | TChangeUnreadNotificationsCount;
