import { IStoreNotification } from '../../types/redux';
import type { IApplicationState } from '../store';

export const getNotificationsStore = (state: IApplicationState): IStoreNotification => {
  return state.notifications;
};

export const getIsNotificationsListOpen = (state: IApplicationState): boolean => {
  return state.notifications.isNotificationsListOpen;
};
