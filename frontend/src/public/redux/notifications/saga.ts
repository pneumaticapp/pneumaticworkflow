import {
  ActionChannelEffect,
  ActionPattern,
  actionChannel,
  all,
  call,
  fork,
  put,
  select,
  take,
  takeEvery,
} from 'redux-saga/effects';
import uniqBy from 'lodash.uniqby';

import { getNotifications, TGetNotificationsResponse } from '../../api/getNotifications';
import { removeNotificationItem } from '../../api/removeNotificationItem';
import { markNotificationsAsRead } from '../../api/markNotificationsAsRead';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { isArrayWithItems } from '../../utils/helpers';
import { TRemoveNotificationItem } from '../actions';
import { getNotificationsStore } from '../selectors/notifications';
import { TNotificationsListItem } from '../../types';
import { IStoreNotification } from '../../types/redux';

import {
  ENotificationsActions,
  loadNotificationsListFailed,
  changeNotificationsList,
  TChangeNotificationsList,
  changeHasNewNotifications,
  TLoadNotifications,
  changeUnreadNotificationsCount,
} from './actions';
import { getUnreadNotificationsCount } from '../../api/getUnreadNotificationsCount';
import { NotificationManager } from '../../components/UI/Notifications';

function* fetchNotificationsAsRead() {
  const { items: notificationsList, unreadItemsCount }: IStoreNotification = yield select(
    getNotificationsStore,
  );
  const newNotificationsIds = notificationsList.filter(({ status }) => status === 'new').map(({ id }) => id);

  if (!isArrayWithItems(newNotificationsIds)) {
    return;
  }

  yield put(changeUnreadNotificationsCount(Math.max(0, unreadItemsCount - newNotificationsIds.length)));
  yield call(markNotificationsAsRead, { notifications: newNotificationsIds });
}

function* markAllNotificationsAsRead() {
  const { items: notificationsList }: IStoreNotification = yield select(getNotificationsStore);

  const normalizedNotfications: TNotificationsListItem[] = notificationsList.map((notification) => {
    return { ...notification, status: 'read' };
  });

  yield put(changeNotificationsList({ items: normalizedNotfications }));
}

function* fetchNotifications({ payload: { offset } = { offset: 0 } }: TLoadNotifications) {
  const { items: currentItems }: IStoreNotification = yield select(getNotificationsStore);
  const isEmptyList = offset === 0;

  try {
    const { results: newItems, count: totalItemsCount }: TGetNotificationsResponse = yield getNotifications({ offset });

    if (isEmptyList) {
      const { count: unreadItemsCount } = yield getUnreadNotificationsCount();

      yield put(changeUnreadNotificationsCount(unreadItemsCount));
    }

    const items = uniqBy([...currentItems, ...newItems], 'id');
    const newNotificationsList = { items, count: totalItemsCount };

    yield put(changeNotificationsList(newNotificationsList));
  } catch (error) {
    NotificationManager.notifyApiError(error, { title: 'notifications.fetch-error', message: getErrorMessage(error) });
    console.info('fetch notifications error : ', error);
    yield put(loadNotificationsListFailed());
  }
}

export function* handleRemoveNotification({ payload: { notificationId } }: TRemoveNotificationItem) {
  const { items, totalItemsCount, unreadItemsCount }: IStoreNotification = yield select(
    getNotificationsStore,
  );
  const deletingItem = items.find(({ id }) => id === notificationId);

  if (!deletingItem) {
    return;
  }

  const targetItemsCount = items.length;
  const remainingTotalItemsCount = Math.max(0, totalItemsCount - 1);
  const newItems = items.filter(({ id }) => id !== notificationId);

  yield put(changeNotificationsList({
    items: newItems,
    count: remainingTotalItemsCount,
  }));

  if (deletingItem.status === 'new') {
    yield put(changeUnreadNotificationsCount(Math.max(0, unreadItemsCount - 1)));
  }

  try {
    yield call(removeNotificationItem, { notificationId });
  } catch (error) {
    NotificationManager.notifyApiError(error, {
      title: 'notifications.failed-to-remove-notification',
      message: getErrorMessage(error),
    });
    return;
  }

  const { items: currentItems }: IStoreNotification = yield select(getNotificationsStore);
  const refillItemsCount = Math.min(
    targetItemsCount - currentItems.length,
    remainingTotalItemsCount - currentItems.length,
  );

  if (refillItemsCount <= 0) {
    return;
  }

  try {
    const {
      results: olderItems,
      count: updatedTotalItemsCount,
    }: TGetNotificationsResponse = yield call(getNotifications, {
      offset: currentItems.length,
      limit: refillItemsCount,
    });
    const {
      items: latestItems,
      totalItemsCount: latestTotalItemsCount,
    }: IStoreNotification = yield select(getNotificationsStore);
    const safeTotalItemsCount = latestTotalItemsCount === remainingTotalItemsCount
      ? updatedTotalItemsCount
      : latestTotalItemsCount;

    yield put(changeNotificationsList({
      items: uniqBy([...latestItems, ...olderItems], 'id'),
      count: safeTotalItemsCount,
    }));
  } catch (error) {
    NotificationManager.notifyApiError(error, {
      title: 'notifications.fetch-error',
      message: getErrorMessage(error),
    });
  }
}

function* handleChangeList({ payload: { items: notificationList } }: TChangeNotificationsList) {
  const hasNewNotifications = notificationList.some(({ status }) => status === 'new');

  yield put(changeHasNewNotifications(hasNewNotifications));
}

export function* watchLoadList() {
  yield takeEvery(ENotificationsActions.LoadList, fetchNotifications);
}

export function* watchFetchNotificationsAsRead() {
  yield takeEvery(ENotificationsActions.FetchNotificationsAsRead, fetchNotificationsAsRead);
}

export function* watchMarkNotificationsAsRead() {
  yield takeEvery(ENotificationsActions.MarkNotificationsAsRead, markAllNotificationsAsRead);
}

export function* watchRemoveNotification() {
  const removeNotificationChannel: ActionPattern<ActionChannelEffect> = yield actionChannel(
    ENotificationsActions.RemoveNotificationItem,
  );

  while (true) {
    const action: TRemoveNotificationItem = yield take(removeNotificationChannel);
    yield call(handleRemoveNotification, action);
  }
}

function* watchChangeList() {
  yield takeEvery(ENotificationsActions.ChangeList, handleChangeList);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadList),
    fork(watchMarkNotificationsAsRead),
    fork(watchFetchNotificationsAsRead),
    fork(watchRemoveNotification),
    fork(watchChangeList),
  ]);
}
