import { call, put, select } from 'redux-saga/effects';

import { getActiveUsersCount } from '../../../api/getActiveUsersCount';
import { resendInvite } from '../../../api/resendInvite';
import { NotificationManager } from '../../../components/UI/Notifications';
import { EUserStatus, TUserListItem } from '../../../types/user';
import { activeUsersCountFetchFinished, resendUserInvite } from '../slice';
import { fetchActiveUsersCount, resendUserInviteSaga } from '../saga';
import { getAccountsStore } from '../../selectors/user';
import { setGeneralLoaderVisibility } from '../../general/actions';

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { success: jest.fn(), warning: jest.fn() },
}));
jest.mock('../../../utils/logger', () => ({ logger: { error: jest.fn() } }));

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
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('refreshes tenants count without overwriting local active users count', () => {
    const gen = fetchActiveUsersCount();

    expect(gen.next().value).toEqual(call(getActiveUsersCount));
    expect(gen.next({ activeUsers: 1, tenantsActiveUsers: 4 } as never).value).toEqual(select(getAccountsStore));
    expect(
      gen.next({
        users: [],
        team: { list: [makeUser(1), makeUser(2), makeUser(3, EUserStatus.Invited)] },
      } as never).value,
    ).toEqual(put(activeUsersCountFetchFinished({ activeUsers: 2, tenantsActiveUsers: 4 })));
    expect(gen.next().done).toBe(true);
  });

  it('resends an invite with the general loader and a success notification', () => {
    const gen = resendUserInviteSaga(resendUserInvite(7));

    expect(gen.next().value).toEqual(put(setGeneralLoaderVisibility(true)));
    expect(gen.next().value).toEqual(call(resendInvite, 7));
    expect(gen.next().value).toEqual(put(setGeneralLoaderVisibility(false)));
    expect(NotificationManager.success).toHaveBeenCalledWith({ message: 'team.resend-invite-success-msg' });
    expect(gen.next().done).toBe(true);
  });

  it('warns and hides the loader when resending an invite fails', () => {
    const gen = resendUserInviteSaga(resendUserInvite(7));

    gen.next();
    gen.next();
    expect(gen.throw(new Error('Invite expired')).value).toEqual(put(setGeneralLoaderVisibility(false)));
    expect(NotificationManager.warning).toHaveBeenCalledWith({ message: 'Invite expired' });
    expect(NotificationManager.success).not.toHaveBeenCalledWith({ message: 'team.resend-invite-success-msg' });
  });
});
