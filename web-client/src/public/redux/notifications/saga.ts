/* eslint-disable */
/* prettier-ignore */
import { EventChannel } from 'redux-saga';
import { all, call, fork, put, select, take, takeEvery } from 'redux-saga/effects';
import uniqBy from 'lodash.uniqby';

import { getNotifications, TGetNotificationsResponse } from '../../api/getNotifications';
import { removeNotificationItem } from '../../api/removeNotificationItem';
import { markNotificationsAsRead } from '../../api/markNotificationsAsRead';
import { NotificationManager } from '../../components/UI/Notifications';
import { parseCookies } from '../../utils/cookie';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { isArrayWithItems } from '../../utils/helpers';
import { mergePaths } from '../../utils/urls';
import { TRemoveNotificationItem } from '../actions';
import { getNotificationsStore } from '../selectors/notifications';
import { createWebSocketChannel } from '../utils/createWebSocketChannel';
import { TNotificationsListItem } from '../../types';

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
import { envWssURL } from '../../constants/enviroment';

function* fetchNotificationsAsRead() {
  const {
    items: notificationsList,
    unreadItemsCount,
  }: ReturnType<typeof getNotificationsStore> = yield select(getNotificationsStore);
  const newNotificationsIds = notificationsList.filter(({ status }) => status === 'new').map(({ id }) => id);

  if (!isArrayWithItems(newNotificationsIds)) {
    return;
  }

  yield put(changeUnreadNotificationsCount(Math.max(0, unreadItemsCount - newNotificationsIds.length)));
  yield call(markNotificationsAsRead, { notifications: newNotificationsIds });
}

function* markAllNotificationsAsRead() {
  const { items: notificationsList }: ReturnType<typeof getNotificationsStore> = yield select(getNotificationsStore);

  const normalizedNotfications: TNotificationsListItem[] = notificationsList.map(notification => {
    return { ...notification, status: 'read' };
  });

  yield put(changeNotificationsList({ items: normalizedNotfications }));
}

function* fetchNotifications({ payload: { offset } = { offset: 0 } }: TLoadNotifications) {
  const { items: currentItems }: ReturnType<typeof getNotificationsStore> = yield select(getNotificationsStore);
  const isEmptyList = offset === 0;

  try {
    const {
      results: newItems,
      count: totalItemsCount,
    }: TGetNotificationsResponse = yield getNotifications({ offset });

    if (isEmptyList) {
      const { count: unreadItemsCount } = yield getUnreadNotificationsCount();

      yield put(changeUnreadNotificationsCount(unreadItemsCount));
    }

    const items = uniqBy([...currentItems, ...newItems], 'id');
    const newNotificationsList = { items, count: totalItemsCount };

    yield put(changeNotificationsList(newNotificationsList));
  } catch (error) {
    NotificationManager.error({ title: 'notifications.fetch-error', message: getErrorMessage(error) });
    console.info('fetch notifications error : ', error);
    yield put(loadNotificationsListFailed());
  }
}

function* handleRemoveNotification({ payload: { notificationId } }: TRemoveNotificationItem) {
  const {
    items,
    totalItemsCount,
    unreadItemsCount,
  }: ReturnType<typeof getNotificationsStore> = yield select(getNotificationsStore);
  const newItems = items.filter(({ id }) => id !== notificationId);
  const deletingItem = items.find(({ id }) => id === notificationId);
  if (!deletingItem || items.length === newItems.length) {
    return;
  }

  const newNotificationsList = {
    items: newItems,
    count: totalItemsCount - 1,
  };

  yield put(changeNotificationsList(newNotificationsList));
  if (deletingItem.status === 'new') {
    yield put(changeUnreadNotificationsCount(Math.max(0, unreadItemsCount - 1)));
  }

  try {
    yield call(removeNotificationItem, { notificationId });
  } catch (error) {
    NotificationManager.error({
      title: 'notifications.failed-to-remove-notification',
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

function* watchRemoveNotification() {
  yield takeEvery(ENotificationsActions.RemoveNotificationItem, handleRemoveNotification);
}

function* watchChangeList() {
  yield takeEvery(ENotificationsActions.ChangeList, handleChangeList);
}

export function* watchNewNotifications() {
  const { api: { wsPublicUrl, urls }} = getBrowserConfigEnv();

  const apiUrl = `${urls.wsNotifications}?auth_token=${parseCookies(document.cookie).token}`;
  const url = mergePaths(envWssURL || wsPublicUrl, apiUrl);
  const channel: EventChannel<TNotificationsListItem> = yield call(createWebSocketChannel, url);

  while (true) {
    const newNotification: TNotificationsListItem = yield take(channel);
    const {
      items: currentNotificationsList,
      totalItemsCount,
      unreadItemsCount,
      isNotificationsListOpen,
    }: ReturnType<typeof getNotificationsStore> = yield select(getNotificationsStore);
    const newNotficationsListItems = [newNotification, ...currentNotificationsList];
    yield put(changeNotificationsList({ items: newNotficationsListItems, count: totalItemsCount + 1 }));

    if (!isNotificationsListOpen) {
      yield put(changeUnreadNotificationsCount(unreadItemsCount + 1));
    }
  }
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
