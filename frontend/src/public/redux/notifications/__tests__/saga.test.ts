import { call, put, select } from 'redux-saga/effects';

import { getNotifications, TGetNotificationsResponse } from '../../../api/getNotifications';
import { removeNotificationItem as removeNotificationItemApi } from '../../../api/removeNotificationItem';
import { TNotificationsListItem } from '../../../types';
import { IStoreNotification } from '../../../types/redux';
import { getNotificationsStore } from '../../selectors/notifications';
import {
  changeNotificationsList,
  removeNotificationItem,
} from '../actions';
import { handleRemoveNotification } from '../saga';

const makeNotification = (id: number): TNotificationsListItem => ({
  id,
  status: 'read',
} as TNotificationsListItem);

const makeNotificationsStore = (
  overrides: Partial<IStoreNotification> = {},
): IStoreNotification => ({
  items: [],
  totalItemsCount: 0,
  unreadItemsCount: 0,
  isNotificationsListOpen: true,
  hasNewNotifications: false,
  isLoading: false,
  ...overrides,
});

describe('notifications saga', () => {
  it('loads an older notification after deleting a visible notification', () => {
    const notification = makeNotification(1);
    const olderNotification = makeNotification(2);
    const saga = handleRemoveNotification(
      removeNotificationItem({ notificationId: notification.id }),
    ) as unknown as Generator<unknown, void, IStoreNotification | TGetNotificationsResponse>;

    expect(saga.next().value).toEqual(select(getNotificationsStore));
    expect(saga.next(makeNotificationsStore({
      items: [notification],
      totalItemsCount: 2,
    })).value).toEqual(put(changeNotificationsList({ items: [], count: 1 })));
    expect(saga.next().value).toEqual(call(removeNotificationItemApi, { notificationId: notification.id }));
    expect(saga.next().value).toEqual(select(getNotificationsStore));
    expect(saga.next(makeNotificationsStore({
      totalItemsCount: 1,
    })).value).toEqual(call(getNotifications, { offset: 0, limit: 1 }));
    expect(saga.next({
      results: [olderNotification],
      count: 1,
    }).value).toEqual(select(getNotificationsStore));
    expect(saga.next(makeNotificationsStore({
      totalItemsCount: 1,
    })).value).toEqual(put(changeNotificationsList({
      items: [olderNotification],
      count: 1,
    })));
    expect(saga.next().done).toBe(true);
  });
});
