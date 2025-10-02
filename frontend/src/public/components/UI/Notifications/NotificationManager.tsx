import { EventEmitter } from 'events';

import { createUUID } from '../../../utils/createId';
import { INotification, TAnyFunction } from '../../../types';

const Constants: { [key: string]: INotification['type'] } = {
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error',
};

const DEFAULT_NOTIFY: INotification = {
  id: createUUID(),
  type: 'info',
  title: null,
  message: null,
  timeOut: 5000,
  customClassName: '',
};

/*
  TODO: Refactor this to mapper outside NotificationManager
  https://trello.com/c/E6sXxjT1/1262-handle-notification-colors-properly
*/

const alertErrorMessages = [
  'Something Went Wrong',
  'The transaction was declined. Please use a different card or contact your bank.',
];

class NotificationManagerCreator extends EventEmitter {
  private listNotify: INotification[] = [];

  public create = (notify: INotification) => {
    if (notify.priority) {
      if (notify.message && alertErrorMessages.includes(notify.message.toString())) {
        this.listNotify.unshift({ ...notify, type: 'error' });
      } else {
        this.listNotify.unshift(notify);
      }
    } else if (notify.message && alertErrorMessages.includes(notify.message.toString())) {
      this.listNotify.push({ ...notify, type: 'error' });
    } else {
      this.listNotify.push(notify);
    }
    this.emitChange();
  };

  private notificationCreator = (type: INotification['type']) => (notification?: Partial<INotification>) => {
    if (!notification?.message) {
      return () => {};
    }

    return this.create({
      ...DEFAULT_NOTIFY,
      ...notification,
      id: createUUID(),
      type,
    });
  };

  public success = this.notificationCreator(Constants.SUCCESS);

  public warning = this.notificationCreator(Constants.WARNING);

  public error = this.notificationCreator(Constants.ERROR);

  public remove = (notification: INotification) => {
    this.listNotify = this.listNotify.filter((n) => notification.id !== n.id);
    this.emitChange();
  };

  public emitChange = () => this.emit(Constants.CHANGE, this.listNotify);

  public addChangeListener = (callback: TAnyFunction) => this.addListener(Constants.CHANGE, callback);

  public removeChangeListener = (callback: TAnyFunction) => this.removeListener(Constants.CHANGE, callback);
}

export const NotificationManager = new NotificationManagerCreator();
