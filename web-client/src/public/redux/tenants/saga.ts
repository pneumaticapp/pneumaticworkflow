import { all, fork, takeEvery, takeLatest, put, select } from 'redux-saga/effects';

import { ITenant } from '../../types/tenants';
import { NotificationManager } from '../../components/UI/Notifications';
import { getTenantsSorting } from '../selectors/tenants';
import { getErrorMessage } from '../../utils/getErrorMessage';
import { logger } from '../../utils/logger';

import {
  ETenantsActions,
  TChangeTenantName,
  TCreateTenant,
  TDeleteTenant,
  loadTenants,
  loadTenantsCount,
  loadTenantsCountSuccess,
  loadTenantsFailed,
  loadTenantsSuccess,
  updateTenants,
  updateTenantsCount,
} from './actions';

import { getTenants } from '../../api/tenants/getTenants';
import { createTenant } from '../../api/tenants/createTenant';
import { deleteTenant } from '../../api/tenants/deleteTenant';
import { changeNameTenant } from '../../api/tenants/changeNameTenant';
import { IGetTenantsCountResponse, getTenantsCount } from '../../api/tenants/getTenantsCount';
import { setMenuItemCounter } from '../actions';

function* loadTenantsCountSaga() {
  try {
    const data: IGetTenantsCountResponse = yield getTenantsCount();

    if (data?.count) {
      yield put(loadTenantsCountSuccess(data.count));
      yield put(
        setMenuItemCounter({
          id: 'tenants',
          value: data.count,
          type: 'info',
        }),
      );
    }
  } catch (error) {
    yield put(loadTenantsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load tenants count', error);
  }
}

function* updateTenantsCountSaga() {
  yield put(loadTenantsCount());
}

function* loadTenantsSaga() {
  const sorting: ReturnType<typeof getTenantsSorting> = yield select(getTenantsSorting);

  try {
    const tenants: ITenant[] = yield getTenants({ sorting });
    yield put(loadTenantsSuccess(tenants));
  } catch (error) {
    yield put(loadTenantsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to load tenants', error);
  }
}

function* changeSortingSaga() {
  yield put(loadTenants());
}

function* updateTenantsSaga() {
  yield put(loadTenants());
}

function* createTenantSaga({ payload: name }: TCreateTenant) {
  try {
    yield createTenant({ name });
    yield put(updateTenants());
    yield put(updateTenantsCount());
  } catch (error) {
    yield put(loadTenantsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to create tenant', error);
  }
}

function* deleteTenantSaga({ payload: id }: TDeleteTenant) {
  try {
    yield deleteTenant({ id });
    yield put(updateTenants());
    yield put(updateTenantsCount());
  } catch (error) {
    yield put(loadTenantsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to delete tenant', error);
  }
}

function* changeNameTenantSaga({ payload: { id, name } }: TChangeTenantName) {
  try {
    yield changeNameTenant({ id, name });
    yield put(updateTenants());
  } catch (error) {
    yield put(loadTenantsFailed());
    NotificationManager.warning({ message: getErrorMessage(error) });
    logger.error('failed to change name tenant', error);
  }
}

export function* watchCreateTenant() {
  yield takeEvery(ETenantsActions.CreateTenant, createTenantSaga);
}

export function* watchDeleteTenant() {
  yield takeEvery(ETenantsActions.DeleteTenant, deleteTenantSaga);
}

export function* watchChangeNameTenant() {
  yield takeEvery(ETenantsActions.ChangeTenantName, changeNameTenantSaga);
}

export function* watchUpdateTenants() {
  yield takeEvery(ETenantsActions.UpdateTenants, updateTenantsSaga);
}

export function* watchLoadTenantsCount() {
  yield takeEvery(ETenantsActions.LoadTenantsCount, loadTenantsCountSaga);
}

export function* watchUpdateTenantsCount() {
  yield takeEvery(ETenantsActions.UpdateTenantsCount, updateTenantsCountSaga);
}

export function* watchLoadTenants() {
  yield takeEvery(ETenantsActions.LoadTenants, loadTenantsSaga);
}

export function* watchChangeTenantsSorting() {
  yield takeLatest(ETenantsActions.ChangeTenantsSorting, changeSortingSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchLoadTenantsCount),
    fork(watchUpdateTenantsCount),
    fork(watchLoadTenants),
    fork(watchChangeTenantsSorting),
    fork(watchUpdateTenants),
    fork(watchChangeNameTenant),
    fork(watchDeleteTenant),
    fork(watchCreateTenant),
  ]);
}
