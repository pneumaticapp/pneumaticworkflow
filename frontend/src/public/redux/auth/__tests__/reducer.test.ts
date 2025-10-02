import { EUserStatus } from '../../../types/user';

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfig: () => ({
    googleAuthUserInfo: {},
    invitedUser: {},
  }),
}));
import { INIT_STATE, reducer } from '../reducer';
import {
  authUserFail,
  authUserSuccess,
  loginUser,
  registerUserSuccess,
  removeGoogleUser,
  TAuthActions,
  EAuthUserFailType,
} from '../actions';
import { ESubscriptionPlan } from '../../../types/account';
import { ELoggedState, IAuthUser } from '../../../types/redux';

const mockUser = {
  id: 9,
  isAdmin: true,
  account: { name: 'User Corp', billingPlan: ESubscriptionPlan.Free, planExpiration: null },
  email: 'mock@usercorp.com',
  token: 'token',
  firstName: 'User',
  lastName: 'Unknown',
  phone: '+78005553535',
  photo: '/url/to/photo.jpg',
  status: EUserStatus.Deleted,
} as Omit<IAuthUser, 'loading'>;

describe('auth reducer', () => {
  it('returns the default state', () => {
    const result = reducer(undefined, 'NOT_ACTION' as unknown as TAuthActions);

    expect(result).toEqual(INIT_STATE);
  });
  it('on user login, returns a new state with the loading flag set to active', () => {
    const action = loginUser({ email: 'example@pneumatic.app', password: 'test' });

    const result = reducer(INIT_STATE, action);

    expect(result).toHaveProperty('loading', true);
  });
  it('upon successful user login, returns a new state with user data', () => {
    const action = authUserSuccess(mockUser);

    const result = reducer(INIT_STATE, action);

    expect(result).toEqual({ ...INIT_STATE, ...mockUser, loggedState: ELoggedState.LoggedIn });
  });
  it('upon unsuccessful user login, returns a new state with an error flag ', () => {
    const action = authUserFail();

    const result = reducer(INIT_STATE, action);

    expect(result).toEqual({ ...INIT_STATE, error: EAuthUserFailType.Common, loading: false });
  });
  it('upon successful user registration, returns a new state with user data', () => {
    const action = registerUserSuccess(mockUser);
    const state = { ...INIT_STATE, loading: true };

    const result = reducer(state, action);

    expect(result).toEqual({ ...state, loading: false, ...mockUser });
  });
  it('when deleting data about a Google user, Google authentication data is also removed', () => {
    const action = removeGoogleUser();
    const googleAuthUserInfo = { email: 'ex@gmail.com', firstName: 'Ex', lastName: 'Fed' };
    const state = { ...INIT_STATE, googleAuthUserInfo };

    const result = reducer(state, action);

    expect(result).toEqual({ ...state, googleAuthUserInfo: {} });
  });
});
