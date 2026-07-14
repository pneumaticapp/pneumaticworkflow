import { select, put } from "redux-saga/effects";
import { getNotificationsStore } from "../../selectors/notifications";
import { changeNotificationsList, changeUnreadNotificationsCount } from "../../notifications/actions";
import type { TNotificationsListItem } from "../../../types";

export function* prependNotificationItem(item: TNotificationsListItem) {
  const {
    items: currentNotificationsList,
    totalItemsCount,
    unreadItemsCount,
    isNotificationsListOpen,
  }: ReturnType<typeof getNotificationsStore> = yield select(getNotificationsStore);
  const nextItems = [item, ...currentNotificationsList];
  yield put(changeNotificationsList({ items: nextItems, count: totalItemsCount + 1 }));
  
  if (!isNotificationsListOpen) {
    yield put(changeUnreadNotificationsCount(unreadItemsCount + 1));
  }
}