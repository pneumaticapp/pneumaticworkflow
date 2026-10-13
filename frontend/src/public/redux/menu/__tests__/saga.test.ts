import { put, select } from 'redux-saga/effects';

import { setMenuItemCounter } from '../actions';
import { updateCounterSaga } from '../saga';
import { teamFetchFinished, usersFetchFinished } from '../../accounts/slice';
import { getTotalTasksCount } from '../../selectors/tasks';
import { getAccountPlan } from '../../selectors/accounts';
import { getTenantsCountStore } from '../../selectors/tenants';
import { IAccountPlan } from '../../../types/redux';

const plan = { activeUsers: 3 } as IAccountPlan;

describe('menu counter saga', () => {
  it('updates team counter after users list changes', () => {
    const gen = updateCounterSaga(usersFetchFinished([]));

    expect(gen.next().value).toEqual(select(getTotalTasksCount));
    expect(gen.next(0 as never).value).toEqual(select(getAccountPlan));
    expect(gen.next(plan as never).value).toEqual(select(getTenantsCountStore));
    expect(gen.next(0 as never).value).toEqual(put(setMenuItemCounter({ id: 'team', value: 3, type: 'info' })));
    expect(gen.next().value).toEqual(put(setMenuItemCounter({ id: 'tenants', value: 0, type: 'info' })));
    expect(gen.next().done).toBe(true);
  });

  it('updates team counter after team list changes', () => {
    const gen = updateCounterSaga(teamFetchFinished([]));

    expect(gen.next().value).toEqual(select(getTotalTasksCount));
    expect(gen.next(0 as never).value).toEqual(select(getAccountPlan));
    expect(gen.next(plan as never).value).toEqual(select(getTenantsCountStore));
    expect(gen.next(0 as never).value).toEqual(put(setMenuItemCounter({ id: 'team', value: 3, type: 'info' })));
  });
});
