jest.mock('../../api/saveFirebaseDeviceToken', () => ({
  saveFirebaseDeviceToken: jest.fn(),
}));

jest.mock('../../api/resetFirebaseDeviceToken', () => ({
  resetFirebaseDeviceToken: jest.fn(),
}));

import { saveFirebaseDeviceToken as saveFirebaseDeviceTokenAPI } from '../../api/saveFirebaseDeviceToken';
import { resetFirebaseDeviceToken as resetFirebaseDeviceTokenAPI } from '../../api/resetFirebaseDeviceToken';
import { FIREBASE_DEVICE_STORAGE_KEY, saveFirebaseDeviceToken, resetFirebaseDeviceToken } from '../utils';

const mockSaveApi = saveFirebaseDeviceTokenAPI as jest.MockedFunction<typeof saveFirebaseDeviceTokenAPI>;
const mockResetApi = resetFirebaseDeviceTokenAPI as jest.MockedFunction<typeof resetFirebaseDeviceTokenAPI>;

describe('firebase utils: save and reset device token', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('saveFirebaseDeviceToken', () => {
    it('sends token via API and saves it to localStorage', () => {
      const token = 'test-token-save-123';
      saveFirebaseDeviceToken(token);

      expect(mockSaveApi).toHaveBeenCalledTimes(1);
      expect(mockSaveApi).toHaveBeenCalledWith(token);
      expect(localStorage.getItem(FIREBASE_DEVICE_STORAGE_KEY)).toBe(token);
    });
  });

  describe('resetFirebaseDeviceToken', () => {
    it('does not call API when token is not present in localStorage', async () => {
      await resetFirebaseDeviceToken();

      expect(mockResetApi).toHaveBeenCalledTimes(0);
    });

    it('calls API and removes token from localStorage when token is present', async () => {
      const token = 'test-token-reset-456';
      localStorage.setItem(FIREBASE_DEVICE_STORAGE_KEY, token);

      await resetFirebaseDeviceToken();

      expect(mockResetApi).toHaveBeenCalledTimes(1);
      expect(mockResetApi).toHaveBeenCalledWith(token);
      expect(localStorage.getItem(FIREBASE_DEVICE_STORAGE_KEY)).toBeNull();
    });
  });
});
