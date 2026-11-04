import { IStoreNotification } from '../../types/redux';
import type { RootState } from '../store';

export const getNotificationsStore = (state: RootState): IStoreNotification => {
  return state.notifications;
};

export const getIsNotificationsListOpen = (state: RootState): boolean => {
  return state.notifications.isNotificationsListOpen;
};
