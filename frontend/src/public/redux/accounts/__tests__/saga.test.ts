import { call, put, select } from 'redux-saga/effects';

import { getActiveUsersCount } from '../../../api/getActiveUsersCount';
import { EUserStatus, TUserListItem } from '../../../types/user';
import { activeUsersCountFetchFinished } from '../slice';
import { fetchActiveUsersCount } from '../saga';
import { getAccountsStore } from '../../selectors/user';

const makeUser = (id: number, status = EUserStatus.Active): TUserListItem => ({
  id,
  firstName: `User ${id}`,
  lastName: '',
  email: `user-${id}@test.com`,
  phone: '',
  photo: '',
  status,
  type: 'user',
  isAdmin: false,
  isAccountOwner: false,
});

describe('accounts saga', () => {
  it('refreshes tenants count without overwriting local active users count', () => {
    const gen = fetchActiveUsersCount();

    expect(gen.next().value).toEqual(call(getActiveUsersCount));
    expect(gen.next({ activeUsers: 1, tenantsActiveUsers: 4 } as never).value).toEqual(select(getAccountsStore));
    expect(gen.next({
      users: [],
      team: { list: [makeUser(1), makeUser(2), makeUser(3, EUserStatus.Invited)] },
    } as never).value).toEqual(put(activeUsersCountFetchFinished({ activeUsers: 2, tenantsActiveUsers: 4 })));
    expect(gen.next().done).toBe(true);
  });
});
