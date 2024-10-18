import { configMock } from '../../../__stubs__/configMock';
jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue(configMock),
  getBrowserConfig: jest.fn().mockReturnValue(configMock),
}));
import {
  loginWithEmailPasswordAsync,
  registerInviteAsync,
  registerWithEmailAsync,
  registerWithEmailPassword,
  registerWithInvite,
} from '../saga';
import { registerUser, registerUserInvited } from '../actions';
import { setJwtCookie } from '../../../utils/authCookie';
import { setOAuthRegistrationCompleted } from '../../../api/setOAuthRegistrationCompleted';
import { getOAuthId, getOAuthType } from '../../../utils/auth';
import { EOAuthType } from '../../../types/auth';

const auth = {
  createUserWithEmail: jest.fn(),
  signInWithEmailAndPassword: jest.fn(),
  createUserWithInvite: jest.fn(),
};
jest.mock('../../../utils/auth');
jest.mock('../../../api/setOAuthRegistrationCompleted');
jest.mock('../../../utils/authCookie');
jest.mock('../../../api/auth', () => ({
  get auth() {
    return auth;
  },
}));

const mockRegisterData = {
  email: 'example@pneumatic.app',
  firstName: 'A',
  lastName: 'Z',
  companyName: 'A-Z',
  photo: '/some/photo.jpg',
  fromEmail: true,
  password: 'test_pwd',
  timezone: ''
};

describe('saga', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    jest.clearAllMocks();
    jest.resetModules();
  });
  describe('loginWithEmailPasswordAsync', () => {
    it('возврвщает завершившийся успешно промис логина', async () => {
      const authUser = { access: 'some-token-string' };
      auth.signInWithEmailAndPassword.mockResolvedValueOnce(authUser);
      const [email, password] = ['example@pneumatic.app', 'somEpAssw0rD!'];

      const result = loginWithEmailPasswordAsync(email, password);

      expect(auth.signInWithEmailAndPassword).toHaveBeenCalledWith(email, password);
      await expect(result).resolves.toEqual(authUser);
    });
    it('возврвщает завершившийся неудачно промис логина', async () => {
      const error = { error: 'unknown error' };
      auth.signInWithEmailAndPassword.mockRejectedValueOnce(error);
      const [email, password] = ['example@pneumatic.app', 'somEpAssw0rD!'];

      const result = loginWithEmailPasswordAsync(email, password);

      expect(auth.signInWithEmailAndPassword).toHaveBeenCalledWith(email, password);
      await expect(result).resolves.toEqual(error);
    });
  });
  describe('registerWithEmailAsync', () => {
    it('возврвщает завершившийся успешно промис регистрации', async () => {
      const authUser = { access: 'some-token-string' };
      auth.createUserWithEmail.mockResolvedValueOnce(authUser);

      const result = registerWithEmailAsync(mockRegisterData);

      expect(auth.createUserWithEmail).toHaveBeenCalledWith(mockRegisterData, undefined, undefined);
      await expect(result).resolves.toEqual(authUser);
    });
    it('возврвщает завершившийся неудачно промис регистрации', async () => {
      const error = { error: 'unknown error' };
      auth.createUserWithEmail.mockRejectedValueOnce(error);

      const result = registerWithEmailAsync(mockRegisterData);

      expect(auth.createUserWithEmail).toHaveBeenCalledWith(mockRegisterData, undefined, undefined);
      await expect(result).resolves.toEqual(error);
    });
  });
  describe('registerInviteAsync', () => {
    const id = 'ad1930f2-9c8e-4018-bb77-39ab9990e1b1';
    it('возврвщает завершившийся успешно промис регистрации по инвайту', async () => {
      const authUser = { access: 'some-token-string' };
      auth.createUserWithInvite.mockResolvedValueOnce(authUser);

      const result = registerInviteAsync(id, mockRegisterData);

      expect(auth.createUserWithInvite).toHaveBeenCalledWith(id, mockRegisterData);
      await expect(result).resolves.toEqual(authUser);
    });
    it('возврвщает завершившийся неудачно промис регистрации по инвайту', async () => {
      const error = { error: 'unknown error' };
      auth.createUserWithInvite.mockRejectedValueOnce(error);

      const result = registerInviteAsync(id, mockRegisterData);

      expect(auth.createUserWithInvite).toHaveBeenCalledWith(id, mockRegisterData);
      await expect(result).resolves.toEqual(error);
    });
  });

  describe('registerWithEmailPassword', () => {
    it('регистрирует пользователя и устанавливает полученный токен в виде куки', () => {
      const token = 'some-token';

      const result = registerWithEmailPassword(registerUser({ user: mockRegisterData }));
      result.next();
      result.next({ token } as any);
      result.next();

      expect(setJwtCookie).toHaveBeenCalledWith(token);
    });
    it('если произошла успешная регистрация гугл-пользователя вызывает завершение регистрации', () => {
      const id = 'ad1930f2-9c8e-4018-bb77-39ab9990e1b1';
      const token = 'some-token';
      (getOAuthId as jest.Mock).mockReturnValueOnce(id);
      (getOAuthType as jest.Mock).mockReturnValueOnce(EOAuthType.Google);
      (setOAuthRegistrationCompleted as jest.Mock).mockRejectedValueOnce('fail');

      const result = registerWithEmailPassword(registerUser({ user: mockRegisterData }));
      result.next();
      result.next({ token } as any);
      result.next();

      expect(setJwtCookie).toHaveBeenCalledWith(token);
      expect(setOAuthRegistrationCompleted).toHaveBeenCalledWith(id, EOAuthType.Google);
    });
    it('при неудачной регистрации выводит полученное сообщение', () => {
      const message = 'FAIL';
      const info = jest.spyOn(console, 'info');

      const result = registerWithEmailPassword(registerUser({ user: mockRegisterData }));
      result.next();
      result.next({ message } as any);
      result.next();

      expect(info).toHaveBeenCalledWith('register failed :', message);
    });
    it('если запрос ничего не вернул выводит ошибку', () => {
      const result = registerWithEmailPassword(registerUser({ user: mockRegisterData }));
      result.next();
      result.next();
    });
  });
  describe('registerWithInvite', () => {
    const id = 'ad1930f2-9c8e-4018-bb77-39ab9990e1b1';
    it('регистрирует пользователя и устанавливает полученный токен в виде куки', () => {
      const token = 'some-token';

      const result = registerWithInvite(registerUserInvited(mockRegisterData));
      result.next();
      result.next({ invitedUser: { id } } as any);
      result.next({ token } as any);
      result.next();

      expect(setJwtCookie).toHaveBeenCalledWith(token);
    });
    it('при неудачной регистрации выводит полученное сообщение', () => {
      const message = 'FAIL';
      const info = jest.spyOn(console, 'info');

      const result = registerWithInvite(registerUserInvited(mockRegisterData));
      result.next();
      result.next({ invitedUser: { id } } as any);
      result.next({ message } as any);
      result.next();

      expect(info).toHaveBeenCalledWith('register failed :', message);
    });
    it('если пришёл пустой ответ, то вызывает событие неудавшейся регистрации', () => {
      const result = registerWithInvite(registerUserInvited(mockRegisterData));
      result.next();
      result.next({ invitedUser: { invite_id: id } } as any);
      result.next(true as any);
      result.next();
      result.next();
    });
    it('если нет id, ничего вызывает событие неудачной регистрации', () => {
      const result = registerWithInvite(registerUserInvited(mockRegisterData));
      result.next();
      result.next({ invitedUser: {} } as any);
      result.next(true as any);
      result.next();
    });
  });
});
