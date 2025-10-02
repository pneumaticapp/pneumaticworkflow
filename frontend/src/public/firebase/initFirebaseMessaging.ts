import { initializeApp } from 'firebase/app';
import { getMessaging, getToken } from 'firebase/messaging';

import { saveFirebaseDeviceToken } from './utils';

import { getBrowserConfig } from '../utils/getConfig';

export function initFirebaseMessaging() {
  const { config: { firebase: { vapidKey, config } } } = getBrowserConfig();

  // Notification is undefined in some browsers. This check is crucial.
  if (typeof Notification === 'undefined') {
    return;
  }

  Promise.resolve(Notification?.requestPermission()).then((permission) => {
    if (permission === 'granted') {
      const app = initializeApp(config);
      const messaging = getMessaging(app);
      getToken(messaging, { vapidKey }).then((token) => {
        if (token) {
          saveFirebaseDeviceToken(token);
        }
      });
    }
  });
}
