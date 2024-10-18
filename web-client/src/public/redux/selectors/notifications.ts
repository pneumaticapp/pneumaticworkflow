import { IApplicationState, IStoreNotification } from '../../types/redux';

export const getNotificationsStore = (state: IApplicationState): IStoreNotification => {
  return state.notifications;
};

export const getIsNotificationsListOpen = (state: IApplicationState): boolean => {
  return state.notifications.isNotificationsListOpen;
};
