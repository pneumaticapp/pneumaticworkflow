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
  it('возвращает стейт по умолчанию', () => {
    const result = reducer(undefined, 'NOT_ACTION' as unknown as TAuthActions);

    expect(result).toEqual(INIT_STATE);
  });
  it('при логине пользователя возвращает новый стейт с активным флагом загрузки', () => {
    const action = loginUser({ email: 'example@pneumatic.app', password: 'test' });

    const result = reducer(INIT_STATE, action);

    expect(result).toHaveProperty('loading', true);
  });
  it('при успешном логине пользователя возвращает новый стейт с данными о пользователе', () => {
    const action = authUserSuccess(mockUser);

    const result = reducer(INIT_STATE, action);

    expect(result).toEqual({ ...INIT_STATE, ...mockUser, loggedState: ELoggedState.LoggedIn });
  });
  it('при неудачном логине пользователя возвращает новый стейт с флагом ошибки ', () => {
    const action = authUserFail();

    const result = reducer(INIT_STATE, action);

    expect(result).toEqual({ ...INIT_STATE, error: EAuthUserFailType.Common, loading: false });
  });
  it('при успешной регистрации пользователя возвращает новый стейт с данными о пользователе', () => {
    const action = registerUserSuccess(mockUser);
    const state = { ...INIT_STATE, loading: true };

    const result = reducer(state, action);

    expect(result).toEqual({ ...state, loading: false, ...mockUser });
  });
  it('при удалении данных о гугл пользователе удаляются данные Google авторизации', () => {
    const action = removeGoogleUser();
    const googleAuthUserInfo = { email: 'ex@gmail.com', firstName: 'Ex', lastName: 'Fed' };
    const state = { ...INIT_STATE, googleAuthUserInfo };

    const result = reducer(state, action);

    expect(result).toEqual({ ...state, googleAuthUserInfo: {} });
  });
});
