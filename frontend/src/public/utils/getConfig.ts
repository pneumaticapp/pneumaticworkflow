/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:no-any */
const commonConfig = require('../../../config/common.json');

import { IUnsavedUser } from '../types/user';
import { IInvitedUser } from '../types/redux';
// @ts-ignore
import * as merge from 'lodash.merge';
import { get, set } from '../../server/utils/helpers';
import { IPages } from '../redux/pages/types';

export type TEnvironment = 'local' | 'staging' | 'prod';

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
  recaptchaSecret: string;
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
  featureFlags: Record<string, string | undefined>;
}

interface IConfig {
  config: IBrowserConfig;
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

type TConfig = typeof commonConfig;

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

export function getConfig(): TConfig {
  const env = (process.env.MCS_RUN_ENV || 'local') as TEnvironment;
  const {
    FRONTEND_URL,
    FORM_DOMAIN,
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
  } = process.env;

  return merge(commonConfig, { env }, {
    "host": FRONTEND_URL,
    "formSubdomain": FORM_DOMAIN,
    "mainPage": SITE_URL,
    "api": {
      "privateUrl": BACKEND_PRIVATE_URL,
      "publicUrl": BACKEND_URL,
      "wsPublicUrl": WSS_URL
    },
    "analyticsId": ANALYTICS_WRITE_KEY,
    "recaptchaSecret": RECAPTCHA_SITE_KEY,
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
    "featureFlags": {
      "CAPTCHA": process.env.CAPTCHA,
      "GOOGLE_AUTH": process.env.GOOGLE_AUTH,
      "MS_AUTH": process.env.MS_AUTH,
      "SSO_AUTH": process.env.SSO_AUTH,
      "SIGNUP": process.env.SIGNUP,
      "BILLING": process.env.BILLING,
      "AI": process.env.AI,
      "PUSH": process.env.PUSH,
      "STORAGE": process.env.STORAGE,
      "ANALYTICS": process.env.ANALYTICS,
      "SSO_PROVIDER": process.env.SSO_PROVIDER,
      "LANGUAGE_CODE": process.env.LANGUAGE_CODE,
      "BACKEND_URL": process.env.BACKEND_URL,
      "SENTRY_DSN": process.env.SENTRY_DSN,
      "WSS_URL": process.env.WSS_URL,
      "HOST": process.env.HOST,
      "ANALYTICS_ID": process.env.ANALYTICS_ID,
      "RECAPTCHA_SITE_KEY": process.env.RECAPTCHA_SITE_KEY,
      "GOOGLE_CLIENT_ID": process.env.GOOGLE_CLIENT_ID,
      "FIREBASE_VAPID_KEY": process.env.FIREBASE_VAPID_KEY,
      "FIREBASE_API_KEY": process.env.FIREBASE_API_KEY,
      "FIREBASE_AUTH_DOMAIN": process.env.FIREBASE_AUTH_DOMAIN,
      "FIREBASE_PROJECT_ID": process.env.FIREBASE_PROJECT_ID,
      "FIREBASE_STORAGE_BUCKET": process.env.FIREBASE_STORAGE_BUCKET,
      "FIREBASE_SENDER_ID": process.env.FIREBASE_SENDER_ID,
      "FIREBASE_APP_ID": process.env.FIREBASE_APP_ID,
      "FIREBASE_MEASUREMENT_ID": process.env.FIREBASE_MEASUREMENT_ID,
      "SENTRY_RELEASE": process.env.SENTRY_RELEASE
    }
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
