/// <reference types="jest" />
import { updateTemplate } from '../../../api/updateTemplate';
import { NotificationManager } from '../../../components/UI/Notifications';
import { logger } from '../../../utils/logger';
import { createOrUpdateTemplate } from '../saga';
import { allocateAutosavePersistRequest, createAutosavePersistScope } from '../persistRequest';

jest.mock('../../../api/updateTemplate', () => ({ updateTemplate: jest.fn() }));
jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { notifyApiError: jest.fn() },
}));
jest.mock('../../../utils/logger', () => ({
  logger: { error: jest.fn() },
}));

describe('createOrUpdateTemplate', () => {
  it('suppresses failure side effects for a superseded autosave', () => {
    const scope = createAutosavePersistScope();
    const request = allocateAutosavePersistRequest(scope);
    const saga = createOrUpdateTemplate({ id: 1 } as any, true, [], request);

    saga.next();
    allocateAutosavePersistRequest(scope);
    const result = saga.throw(new Error('stale request failed'));

    expect(result.done).toBe(true);
    expect(updateTemplate).toHaveBeenCalledTimes(1);
    expect(logger.error).not.toHaveBeenCalled();
    expect(NotificationManager.notifyApiError).not.toHaveBeenCalled();
  });
});
