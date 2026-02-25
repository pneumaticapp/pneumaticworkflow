/* eslint-disable no-restricted-syntax */
import { all, fork, put, select, takeEvery } from 'redux-saga/effects';
import { PayloadAction } from '@reduxjs/toolkit';
import { EMenuActions, mergeMenuItems, setMenuItemCounter } from './actions';
import { activeUsersCountFetchFinished, setCurrentPlan } from '../accounts/slice';
import { TActiveUsersCountFetchFinishedPayload } from '../accounts/types';
import { IAccountPlan } from '../../types/redux';
import { getAuthUser } from '../selectors/user';
import { generateMenuItems, createMenuCounter } from '../../utils/menu';
import { IMenuItem } from '../../types/menu';
import { getTotalTasksCount } from '../selectors/tasks';
import { getAccountPlan } from '../selectors/accounts';
import { TMenuCounter } from '../../constants/menu';
import { changeTasksCount } from '../tasks/slice';

import { getTenantsCountStore } from '../selectors/tenants';

export function* generateMenuSaga() {
  try {
    const { authUser }: ReturnType<typeof getAuthUser> = yield select(getAuthUser);

    // set the menu items sequentially: first the top-level items, and then the sub-items
    for (const menuItemsPromise of generateMenuItems(authUser)) {
      const menuItems: IMenuItem[] = yield menuItemsPromise;
      yield put(mergeMenuItems(menuItems));
    }
  } catch (error) {
    console.info('fetch menu error : ', error);
  }
}

type TUpdateCounterAction = PayloadAction<number>  | PayloadAction<TActiveUsersCountFetchFinishedPayload> | PayloadAction<IAccountPlan>;

export function* updateCounterSaga(action: TUpdateCounterAction) {
  const tasksCount: ReturnType<typeof getTotalTasksCount> = yield select(getTotalTasksCount);
  const { activeUsers: teamCount }: ReturnType<typeof getAccountPlan> = yield select(getAccountPlan);
  const tenantCount: ReturnType<typeof getTenantsCountStore> = yield select(getTenantsCountStore);

  const getCounterByActionMap: { check(): boolean; getCounters(): TMenuCounter[] }[] = [
    {
      check: () => action.type === changeTasksCount.type,
      getCounters: () => [createMenuCounter('tasks', tasksCount, 'alert')].filter(Boolean) as TMenuCounter[],
    },
    {
      check: () =>
        [activeUsersCountFetchFinished.type, setCurrentPlan.type].some(
          (t) => t === action.type,
        ),
      getCounters: () =>
        [createMenuCounter('team', teamCount), createMenuCounter('tenants', tenantCount)].filter(
          Boolean,
        ) as TMenuCounter[],
    },
  ];

  const counters = getCounterByActionMap.find(({ check }) => check())?.getCounters() || [];

  for (const counter of counters) {
    yield put(setMenuItemCounter(counter));
  }
}

export function* watchLoadMenu() {
  yield takeEvery(EMenuActions.GenerateMenu, generateMenuSaga);
}

export function* watchUpdateCounter() {
  yield takeEvery(
    [
      changeTasksCount.type,
      activeUsersCountFetchFinished.type,
      setCurrentPlan.type,
    ],
    updateCounterSaga,
  );
}

export function* rootSaga() {
  yield all([fork(watchLoadMenu), fork(watchUpdateCounter)]);
}
