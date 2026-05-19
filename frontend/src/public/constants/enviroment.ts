const getEnvVar = (key: string): string | undefined => {
  if (typeof window !== 'undefined') {
    // eslint-disable-next-line no-underscore-dangle
    const pneumaticConfig = (window as any).__pneumaticConfig;
    if (pneumaticConfig?.config?.featureFlags && pneumaticConfig.config.featureFlags[key] !== undefined) {
      return pneumaticConfig.config.featureFlags[key];
    }
  }
  if (typeof process !== 'undefined' && process.env) {
    return process.env[key];
  }
  return undefined;
};

export const envLanguageCode: string | undefined  =     getEnvVar('LANGUAGE_CODE');
export const envBackendURL: string | undefined =        getEnvVar('BACKEND_URL');
export const envSentry: string | undefined =            getEnvVar('SENTRY_DSN');
export const envWssURL: string | undefined =            getEnvVar('WSS_URL');
export const envDevMode: boolean =  process.env.NODE_ENV === 'development';

export const isEnvCaptcha: boolean =    getEnvVar('CAPTCHA') !== 'no';
export const isEnvGoogleAuth: boolean = getEnvVar('GOOGLE_AUTH') !== 'no';
export const isEnvMsAuth: boolean =     getEnvVar('MS_AUTH') !== 'no';
export const isEnvSSOAuth: boolean =    getEnvVar('SSO_AUTH') !== 'no';
export const isEnvSignup: boolean =     getEnvVar('SIGNUP') !== 'no';
export const isEnvBilling: boolean =    getEnvVar('BILLING') !== 'no';
export const isEnvAi: boolean =         getEnvVar('AI') !== 'no';
export const isEnvPush: boolean =       getEnvVar('PUSH') !== 'no';
export const isEnvStorage: boolean =    getEnvVar('STORAGE') !== 'no';
export const isEnvAnalytics: boolean =  getEnvVar('ANALYTICS') !== 'no';
export const envSSOProvider: string | undefined = getEnvVar('SSO_PROVIDER');


// New ENV


export const envHost: string | undefined = getEnvVar('HOST');
export const envAnalyticsId: string | undefined = getEnvVar('ANALYTICS_ID');
export const envRecaptchaSecret: string | undefined = getEnvVar('RECAPTCHA_SITE_KEY');

export const envGoogleClientId: string | undefined = getEnvVar('GOOGLE_CLIENT_ID');
export const envSentryRelease: string | undefined = getEnvVar('SENTRY_RELEASE');

export const envFirebase: any = {
  vapidKey: getEnvVar('FIREBASE_VAPID_KEY'),
  config: {
    apiKey: getEnvVar('FIREBASE_API_KEY'),
    authDomain: getEnvVar('FIREBASE_AUTH_DOMAIN'),
    projectId: getEnvVar('FIREBASE_PROJECT_ID'),
    storageBucket: getEnvVar('FIREBASE_STORAGE_BUCKET'),
    messagingSenderId: getEnvVar('FIREBASE_SENDER_ID'),
    appId: getEnvVar('FIREBASE_APP_ID'),
    measurementId: getEnvVar('FIREBASE_MEASUREMENT_ID')
  }
};
