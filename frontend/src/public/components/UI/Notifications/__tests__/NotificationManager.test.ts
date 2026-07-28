import { NotificationManager } from '../NotificationManager';
import { INotification } from '../../../../types';

describe('NotificationManager', () => {
  describe('notifyApiError', () => {
    it('shows warning for 4xx errors', () => {
      const warningSpy = jest.spyOn(NotificationManager, 'warning');
      const errorSpy = jest.spyOn(NotificationManager, 'error');

      NotificationManager.notifyApiError(
        { status: 400 },
        { message: 'Bad request' },
      );

      expect(warningSpy).toHaveBeenCalledWith({ message: 'Bad request' });
      expect(errorSpy).not.toHaveBeenCalled();

      warningSpy.mockRestore();
      errorSpy.mockRestore();
    });

    it('shows error for 5xx errors', () => {
      const errorSpy = jest.spyOn(NotificationManager, 'error');
      const warningSpy = jest.spyOn(NotificationManager, 'warning');

      NotificationManager.notifyApiError(
        { status: 500 },
        { message: 'Internal server error' },
      );

      expect(errorSpy).toHaveBeenCalledWith({ message: 'Internal server error' });
      expect(warningSpy).not.toHaveBeenCalled();

      errorSpy.mockRestore();
      warningSpy.mockRestore();
    });

    it('shows warning when status is undefined', () => {
      const warningSpy = jest.spyOn(NotificationManager, 'warning');
      const errorSpy = jest.spyOn(NotificationManager, 'error');

      NotificationManager.notifyApiError(
        {},
        { message: 'Unknown error' },
      );

      expect(warningSpy).toHaveBeenCalledWith({ message: 'Unknown error' });
      expect(errorSpy).not.toHaveBeenCalled();

      warningSpy.mockRestore();
      errorSpy.mockRestore();
    });

    it('shows warning for File Service 413 (FILE_003)', () => {
      const warningSpy = jest.spyOn(NotificationManager, 'warning');

      NotificationManager.notifyApiError(
        { status: 413 },
        { message: 'file-service.size-exceeded' },
      );

      expect(warningSpy).toHaveBeenCalledWith({ message: 'file-service.size-exceeded' });
      warningSpy.mockRestore();
    });

    it('shows error for File Service 503 (STORAGE_002)', () => {
      const errorSpy = jest.spyOn(NotificationManager, 'error');

      NotificationManager.notifyApiError(
        { status: 503 },
        { message: 'file-service.upload-failed' },
      );

      expect(errorSpy).toHaveBeenCalledWith({ message: 'file-service.upload-failed' });
      errorSpy.mockRestore();
    });

    it('shows warning for File Service 401 (AUTH_001)', () => {
      const warningSpy = jest.spyOn(NotificationManager, 'warning');

      NotificationManager.notifyApiError(
        { status: 401 },
        { message: 'file-service.auth-failed' },
      );

      expect(warningSpy).toHaveBeenCalledWith({ message: 'file-service.auth-failed' });
      warningSpy.mockRestore();
    });

    it('shows warning for File Service 403 (PERM_001)', () => {
      const warningSpy = jest.spyOn(NotificationManager, 'warning');

      NotificationManager.notifyApiError(
        { status: 403 },
        { message: 'file-service.permission-denied' },
      );

      expect(warningSpy).toHaveBeenCalledWith({ message: 'file-service.permission-denied' });
      warningSpy.mockRestore();
    });

    it('shows warning for File Service 404 (FILE_001)', () => {
      const warningSpy = jest.spyOn(NotificationManager, 'warning');

      NotificationManager.notifyApiError(
        { status: 404 },
        { message: 'file-service.file-not-found' },
      );

      expect(warningSpy).toHaveBeenCalledWith({ message: 'file-service.file-not-found' });
      warningSpy.mockRestore();
    });
  });

  describe('create() preserves notification type without override', () => {
    let changeHandler: jest.Mock;
    let createdId: string;

    beforeEach(() => {
      changeHandler = jest.fn();
      NotificationManager.addChangeListener(changeHandler);
    });

    afterEach(() => {
      NotificationManager.removeChangeListener(changeHandler);
      NotificationManager.remove({ id: createdId } as INotification);
    });

    it('preserves type=warning for "Something Went Wrong" message (alertErrorMessages regression)', () => {
      createdId = 'test-1';
      NotificationManager.create({
        id: createdId,
        type: 'warning',
        title: null,
        message: 'Something Went Wrong',
        timeOut: 5000,
        customClassName: '',
      });

      expect(changeHandler).toHaveBeenCalledTimes(1);
      const notifications = changeHandler.mock.calls[0][0];
      expect(notifications).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ id: 'test-1', type: 'warning', message: 'Something Went Wrong' }),
        ]),
      );
    });

    it('preserves type=warning for payment declined message (alertErrorMessages regression)', () => {
      createdId = 'test-2';
      NotificationManager.create({
        id: createdId,
        type: 'warning',
        title: null,
        message: 'The transaction was declined. Please use a different card or contact your bank.',
        timeOut: 5000,
        customClassName: '',
      });

      expect(changeHandler).toHaveBeenCalledTimes(1);
      const notifications = changeHandler.mock.calls[0][0];
      expect(notifications).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ id: 'test-2', type: 'warning' }),
        ]),
      );
    });
  });
});
