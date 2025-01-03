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
    it('returns a successfully completed login promise', async () => {
      const authUser = { access: 'some-token-string' };
      auth.signInWithEmailAndPassword.mockResolvedValueOnce(authUser);
      const [email, password] = ['example@pneumatic.app', 'somEpAssw0rD!'];

      const result = loginWithEmailPasswordAsync(email, password);

      expect(auth.signInWithEmailAndPassword).toHaveBeenCalledWith(email, password);
      await expect(result).resolves.toEqual(authUser);
    });
    it('returns a failed login promise', async () => {
      const error = { error: 'unknown error' };
      auth.signInWithEmailAndPassword.mockRejectedValueOnce(error);
      const [email, password] = ['example@pneumatic.app', 'somEpAssw0rD!'];

      const result = loginWithEmailPasswordAsync(email, password);

      expect(auth.signInWithEmailAndPassword).toHaveBeenCalledWith(email, password);
      await expect(result).resolves.toEqual(error);
    });
  });
  describe('registerWithEmailAsync', () => {
    it('returns a successfully completed registration promise', async () => {
      const authUser = { access: 'some-token-string' };
      auth.createUserWithEmail.mockResolvedValueOnce(authUser);

      const result = registerWithEmailAsync(mockRegisterData);

      expect(auth.createUserWithEmail).toHaveBeenCalledWith(mockRegisterData, undefined, undefined);
      await expect(result).resolves.toEqual(authUser);
    });
    it('returns a failed registration promise', async () => {
      const error = { error: 'unknown error' };
      auth.createUserWithEmail.mockRejectedValueOnce(error);

      const result = registerWithEmailAsync(mockRegisterData);

      expect(auth.createUserWithEmail).toHaveBeenCalledWith(mockRegisterData, undefined, undefined);
      await expect(result).resolves.toEqual(error);
    });
  });
  describe('registerInviteAsync', () => {
    const id = 'ad1930f2-9c8e-4018-bb77-39ab9990e1b1';
    it('returns a successfully completed invite registration promise', async () => {
      const authUser = { access: 'some-token-string' };
      auth.createUserWithInvite.mockResolvedValueOnce(authUser);

      const result = registerInviteAsync(id, mockRegisterData);

      expect(auth.createUserWithInvite).toHaveBeenCalledWith(id, mockRegisterData);
      await expect(result).resolves.toEqual(authUser);
    });
    it('returns a failed invite registration promise', async () => {
      const error = { error: 'unknown error' };
      auth.createUserWithInvite.mockRejectedValueOnce(error);

      const result = registerInviteAsync(id, mockRegisterData);

      expect(auth.createUserWithInvite).toHaveBeenCalledWith(id, mockRegisterData);
      await expect(result).resolves.toEqual(error);
    });
  });

  describe('registerWithEmailPassword', () => {
    it('registers the user and sets the received token as a cookie', () => {
      const token = 'some-token';

      const result = registerWithEmailPassword(registerUser({ user: mockRegisterData }));
      result.next();
      result.next({ token } as any);
      result.next();

      expect(setJwtCookie).toHaveBeenCalledWith(token);
    });
    it('if the Google user registration is successful, it calls the completion of the registration process', () => {
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
    it('upon unsuccessful registration, displays the received message', () => {
      const message = 'FAIL';
      const info = jest.spyOn(console, 'info');

      const result = registerWithEmailPassword(registerUser({ user: mockRegisterData }));
      result.next();
      result.next({ message } as any);
      result.next();

      expect(info).toHaveBeenCalledWith('register failed :', message);
    });
    it('if the request returns nothing, it displays an error', () => {
      const result = registerWithEmailPassword(registerUser({ user: mockRegisterData }));
      result.next();
      result.next();
    });
  });
  describe('registerWithInvite', () => {
    const id = 'ad1930f2-9c8e-4018-bb77-39ab9990e1b1';
    it('registers the user and sets the received token as a cookie', () => {
      const token = 'some-token';

      const result = registerWithInvite(registerUserInvited(mockRegisterData));
      result.next();
      result.next({ invitedUser: { id } } as any);
      result.next({ token } as any);
      result.next();

      expect(setJwtCookie).toHaveBeenCalledWith(token);
    });
    it('upon unsuccessful registration, it displays the received message', () => {
      const message = 'FAIL';
      const info = jest.spyOn(console, 'info');

      const result = registerWithInvite(registerUserInvited(mockRegisterData));
      result.next();
      result.next({ invitedUser: { id } } as any);
      result.next({ message } as any);
      result.next();

      expect(info).toHaveBeenCalledWith('register failed :', message);
    });
    it('if an empty response is received, it triggers a failed registration event', () => {
      const result = registerWithInvite(registerUserInvited(mockRegisterData));
      result.next();
      result.next({ invitedUser: { invite_id: id } } as any);
      result.next(true as any);
      result.next();
      result.next();
    });
    it('if there is no ID, it triggers a failed registration event.', () => {
      const result = registerWithInvite(registerUserInvited(mockRegisterData));
      result.next();
      result.next({ invitedUser: {} } as any);
      result.next(true as any);
      result.next();
    });
  });
});
