import accountsReducer, {
  activeUsersCountFetchFinished,
  removeUserFromWs,
  teamFetchFinished,
  upsertUserFromWs,
  usersFetchFinished,
} from '../slice';
import { EUserStatus, TUserListItem } from '../../../types/user';

const makeUser = (id: number, firstName: string, status = EUserStatus.Active): TUserListItem => ({
  id,
  firstName,
  lastName: '',
  email: `${firstName.toLowerCase()}@test.com`,
  phone: '',
  photo: '',
  status,
  type: 'user',
  isAdmin: false,
  isAccountOwner: false,
});

describe('accounts reducer realtime users', () => {
  it('keeps websocket users sorted and derives active users count', () => {
    let state = accountsReducer(undefined, activeUsersCountFetchFinished({ activeUsers: 1, tenantsActiveUsers: 0 }));
    state = accountsReducer(state, usersFetchFinished([
      makeUser(1, 'Artyom'),
      makeUser(3, 'very-long-invited-user-email-address@example.com', EUserStatus.Invited),
    ]));
    state = accountsReducer(state, teamFetchFinished(state.users));

    state = accountsReducer(state, upsertUserFromWs(makeUser(2, 'Artyom')));

    expect(state.planInfo.activeUsers).toBe(2);
    expect(state.team.list.map((user) => user.id)).toEqual([1, 2, 3]);
  });

  it('removes websocket deleted user', () => {
    let state = accountsReducer(undefined, activeUsersCountFetchFinished({ activeUsers: 2, tenantsActiveUsers: 0 }));
    state = accountsReducer(state, usersFetchFinished([
      makeUser(1, 'Artyom'),
      makeUser(2, 'Artyom'),
    ]));
    state = accountsReducer(state, teamFetchFinished(state.users));

    state = accountsReducer(state, removeUserFromWs(2));

    expect(state.planInfo.activeUsers).toBe(1);
    expect(state.team.list.map((user) => user.id)).toEqual([1]);
  });

  it('derives active users count from fetched users', () => {
    const state = accountsReducer(undefined, usersFetchFinished([
      makeUser(1, 'Artyom'),
      makeUser(2, 'Invited', EUserStatus.Invited),
    ]));

    expect(state.planInfo.activeUsers).toBe(1);
  });

  it('derives active users count from fetched team users', () => {
    const state = accountsReducer(undefined, teamFetchFinished([
      makeUser(1, 'Artyom'),
      makeUser(2, 'Test'),
      makeUser(3, 'Invited', EUserStatus.Invited),
    ]));

    expect(state.planInfo.activeUsers).toBe(2);
  });
});
