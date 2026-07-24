import { channel as createChannel } from 'redux-saga';
import {
  ActionChannelEffect,
  ActionPattern,
  actionChannel,
  call,
  put,
  select,
  take,
} from 'redux-saga/effects';

import { getNotifications, TGetNotificationsResponse } from '../../../api/getNotifications';
import { removeNotificationItem as removeNotificationItemApi } from '../../../api/removeNotificationItem';
import { TNotificationsListItem } from '../../../types';
import { IStoreNotification } from '../../../types/redux';
import { getNotificationsStore } from '../../selectors/notifications';
import {
  changeNotificationsList,
  ENotificationsActions,
  removeNotificationItem,
  TRemoveNotificationItem,
} from '../actions';
import { handleRemoveNotification, watchRemoveNotification } from '../saga';

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
    const realtimeNotification = makeNotification(3);
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
      items: [realtimeNotification],
      totalItemsCount: 2,
    })).value).toEqual(put(changeNotificationsList({
      items: [realtimeNotification, olderNotification],
      count: 2,
    })));
    expect(saga.next().done).toBe(true);
  });

  it('queues rapid notification removals', () => {
    const action = removeNotificationItem({ notificationId: 1 });
    const channel = createChannel<TRemoveNotificationItem>() as unknown as ActionPattern<ActionChannelEffect>;
    const saga = watchRemoveNotification() as unknown as Generator<
      unknown,
      void,
      ActionPattern<ActionChannelEffect> | TRemoveNotificationItem
    >;

    expect(saga.next().value).toEqual(actionChannel(ENotificationsActions.RemoveNotificationItem));
    expect(saga.next(channel).value).toEqual(take(channel));
    expect(saga.next(action).value).toEqual(call(handleRemoveNotification, action));
    expect(saga.next().value).toEqual(take(channel));
  });
});
