import { saveFirebaseDeviceToken as saveFirebaseDeviceTokenAPI } from '../api/saveFirebaseDeviceToken';
import { resetFirebaseDeviceToken as resetFirebaseDeviceTokenAPI } from '../api/resetFirebaseDeviceToken';

export const FIREBASE_DEVICE_STORAGE_KEY = 'firebase_device_token';

export const saveFirebaseDeviceToken = (token: string) => {
  saveFirebaseDeviceTokenAPI(token);
  localStorage.setItem(FIREBASE_DEVICE_STORAGE_KEY, token);
};

export const resetFirebaseDeviceToken = () => {
  const savedFirebaseDeviceToken = localStorage.getItem(FIREBASE_DEVICE_STORAGE_KEY);
  if (!savedFirebaseDeviceToken) {
    return;
  }

  resetFirebaseDeviceTokenAPI(savedFirebaseDeviceToken);
  localStorage.setItem(FIREBASE_DEVICE_STORAGE_KEY, "");
};
