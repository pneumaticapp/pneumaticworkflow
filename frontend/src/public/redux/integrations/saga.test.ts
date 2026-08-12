import { call, put } from 'redux-saga/effects';
import { fetchApiKeys, handleCreateApiKey, handleDeleteApiKey } from './saga';
import {
  loadApiKeysSuccess,
  loadApiKeysFailed,
  createApiKeySuccess,
  createApiKeyFailed,
  deleteApiKeySuccess,
  deleteApiKeyFailed,
} from './actions';
import { getApiKeys, createApiKey, deleteApiKey } from '../../api/getApiKey';
import { NotificationManager } from '../../components/UI/Notifications';

jest.mock('../../api/getApiKey');
jest.mock('../../components/UI/Notifications');

describe('integrations saga', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchApiKeys', () => {
    it('handles success', () => {
      const mockApiKeys = [{ id: 1 }];
      const generator = fetchApiKeys();

      expect(generator.next().value).toEqual(call(getApiKeys));
      expect(generator.next(mockApiKeys as any).value).toEqual(put(loadApiKeysSuccess(mockApiKeys as any)));
      expect(generator.next().done).toBe(true);
    });

    it('handles failure', () => {
      const error = new Error('error');
      const generator = fetchApiKeys();

      expect(generator.next().value).toEqual(call(getApiKeys));
      expect(generator.throw(error).value).toEqual(put(loadApiKeysFailed()));
      expect(NotificationManager.notifyApiError).toHaveBeenCalled();
      expect(generator.next().done).toBe(true);
    });
  });

  describe('handleCreateApiKey', () => {
    it('handles success', () => {
      const mockResponse = { id: 1, key: 'pn_live_123', name: 'Test' };
      const action = { type: 'CREATE_API_KEY', payload: { name: 'Test' } } as any;
      const generator = handleCreateApiKey(action);

      expect(generator.next().value).toEqual(call(createApiKey, 'Test'));
      expect(generator.next(mockResponse as any).value).toEqual(
        put(createApiKeySuccess({ apiKey: { id: 1, name: 'Test' } as any, rawKey: 'pn_live_123' }))
      );
      expect(generator.next().done).toBe(true);
    });

    it('handles failure', () => {
      const error = new Error('error');
      const action = { type: 'CREATE_API_KEY', payload: { name: 'Test' } } as any;
      const generator = handleCreateApiKey(action);

      expect(generator.next().value).toEqual(call(createApiKey, 'Test'));
      expect(generator.throw(error).value).toEqual(put(createApiKeyFailed()));
      expect(NotificationManager.notifyApiError).toHaveBeenCalled();
      expect(generator.next().done).toBe(true);
    });
  });

  describe('handleDeleteApiKey', () => {
    it('handles success', () => {
      const action = { type: 'DELETE_API_KEY', payload: { id: 1 } } as any;
      const generator = handleDeleteApiKey(action);

      expect(generator.next().value).toEqual(call(deleteApiKey, 1));
      expect(generator.next().value).toEqual(put(deleteApiKeySuccess({ id: 1 })));
      expect(NotificationManager.success).toHaveBeenCalled();
      expect(generator.next().done).toBe(true);
    });

    it('handles failure', () => {
      const error = new Error('error');
      const action = { type: 'DELETE_API_KEY', payload: { id: 1 } } as any;
      const generator = handleDeleteApiKey(action);

      expect(generator.next().value).toEqual(call(deleteApiKey, 1));
      expect(generator.throw(error).value).toEqual(put(deleteApiKeyFailed()));
      expect(NotificationManager.notifyApiError).toHaveBeenCalled();
      expect(generator.next().done).toBe(true);
    });
  });
});
