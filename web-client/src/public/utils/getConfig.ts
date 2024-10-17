/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:no-any */
const commonConfig = require('../../../config/common.json');
const devConfig = require('../../../config/dev.json');
const prodConfig = require('../../../config/prod.json');

import { IUnsavedUser, TGoogleAuthUserInfo } from '../types/user';
import { IInvitedUser } from '../types/redux';
// @ts-ignore
import * as merge from 'lodash.merge';
import { get, set } from '../../server/utils/helpers';
import { IPages } from '../types/page';

export type TEnvironment = 'local' | 'staging' | 'prod';

const newConfigMap: { [key in TEnvironment]: object } = {
  local: commonConfig,
  staging: devConfig,
  prod: prodConfig,
};

export interface IBrowserConfig {
  host: string;
  api: {
    publicUrl: string;
    wsPublicUrl: string;
    urls: typeof commonConfig.api.urls;
  };
  analyticsId: string;
  mainPage: string;
  formSubdomain: string;
  reсaptchaSecret: string;
  firebase: {
    vapidKey: string;
    config: {
      apiKey: string;
      authDomain: string;
      projectId: string;
      storageBucket: string;
      messagingSenderId: string;
      appId: string;
      measurementId: string;
    };
  };
}

interface IConfig {
  config: IBrowserConfig;
  googleAuthUserInfo: TGoogleAuthUserInfo | {};
  invitedUser: IInvitedUser;
  user: Partial<IUnsavedUser>;
  env?: TEnvironment;
  pages: IPages;
}

interface IPublicFormConfig {
  env?: TEnvironment;
  config: IBrowserConfig;
}

type TWindowWithConfig = Window & typeof globalThis & { __pneumaticConfig: IConfig };
type TWindowWithPublicFormConfig = Window & typeof globalThis & { __pneumaticConfig: IPublicFormConfig };

export function getBrowserConfig() {
  const { __pneumaticConfig } = window as TWindowWithConfig;

  return __pneumaticConfig;
}

export function getPublicFormConfig() {
  const { __pneumaticConfig } = window as TWindowWithPublicFormConfig;

  return __pneumaticConfig;
}

export function getBrowserConfigEnv(): IBrowserConfig {
  const browserConfig = getBrowserConfig();

  return (browserConfig && browserConfig.config) || {};
}

type TConfig = typeof commonConfig & typeof devConfig & typeof prodConfig;

export function getConfig(): TConfig {
  const env = (process.env.MCS_RUN_ENV || 'local') as TEnvironment;
  const {
    FRONTEND_URL,
    FORM_URL,
    SITE_URL,
    BACKEND_PRIVATE_URL,
    BACKEND_URL,
    WSS_URL,
    FIREBASE_VAPID_KEY,
    FIREBASE_API_KEY,
    FIREBASE_AUTH_DOMAIN,
    FIREBASE_PROJECT_ID,
    FIREBASE_STORAGE_BUCKET,
    FIREBASE_SENDER_ID,
    FIREBASE_APP_ID,
    FIREBASE_MEASUREMENT_ID,
    RECAPTCHA_SITE_KEY,
    ANALYTICS_WRITE_KEY,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
  } = process.env;

  return merge(commonConfig, newConfigMap[env], { env }, {
    "host": FRONTEND_URL,
    "formSubdomain": FORM_URL,
    "mainPage": SITE_URL,
    "api": {
      "privateUrl": BACKEND_PRIVATE_URL,
      "publicUrl": BACKEND_URL,
      "wsPublicUrl": WSS_URL
    },
    "google": {
      "clientId": GOOGLE_CLIENT_ID,
      "clientSecret": GOOGLE_CLIENT_SECRET
    },
    "analyticsId": ANALYTICS_WRITE_KEY,
    "reсaptchaSecret": RECAPTCHA_SITE_KEY,
    "firebase": {
      "vapidKey": FIREBASE_VAPID_KEY,
      "config": {
        "apiKey": FIREBASE_API_KEY,
        "authDomain": FIREBASE_AUTH_DOMAIN,
        "projectId": FIREBASE_PROJECT_ID,
        "storageBucket": FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": FIREBASE_SENDER_ID,
        "appId": FIREBASE_APP_ID,
        "measurementId": FIREBASE_MEASUREMENT_ID
      }
    },
  });
}

export function serverConfigToBrowser() {
  const config = getConfig();
  const { exposedToBrowser } = config;
  let resultConfig = {};
  if (!exposedToBrowser || !Array.isArray(exposedToBrowser)) {
    return resultConfig;
  }
  exposedToBrowser.forEach((key: string) => {
    const value = get(config, key);
    if (value) {
      set(resultConfig, key, value);
    }
  });

  return resultConfig;
}
