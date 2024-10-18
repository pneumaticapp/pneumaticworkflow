/* eslint-disable */
/* prettier-ignore */
import { ENotificationsActions, TNotificationsActions } from './actions';
import { IStoreNotification } from '../../types/redux';

const INIT_STATE: IStoreNotification = {
  items: [],
  totalItemsCount: 0,
  unreadItemsCount: 0,
  isNotificationsListOpen: false,
  isLoading: false,
  hasNewNotifications: false,
};

export const reducer = (state = INIT_STATE, action: TNotificationsActions): IStoreNotification => {
  switch (action.type) {
  case ENotificationsActions.LoadList:
    return {
      ...state,
      isLoading: true,
    };
  case ENotificationsActions.ChangeList:
    const { items, count } = action.payload;

    return {
      ...state,
      isLoading: false,
      items,
      totalItemsCount: count || state.totalItemsCount,
    };
  case ENotificationsActions.LoadListFailed:
    return {
      ...state,
      isLoading: false,
    };
  case ENotificationsActions.SetIsOpen: {
    return {
      ...state,
      isNotificationsListOpen: action.payload,
      hasNewNotifications: false,
    };
  }
  case ENotificationsActions.ChangeHasNew: {
    return {
      ...state,
      hasNewNotifications: action.payload,
    };
  }
  case ENotificationsActions.ChangeUnreadCount: {
    return {
      ...state,
      unreadItemsCount: action.payload,
    };
  }

  default: return { ...state };
  }
};
