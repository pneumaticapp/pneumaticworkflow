interface IPneumaticConfig {
  config?: {
    featureFlags?: Record<string, string | undefined>;
  };
}

const getEnv = (key: string): string | undefined => {
  if (typeof window !== 'undefined') {
    // eslint-disable-next-line no-underscore-dangle
    const pneumaticConfig = (window as unknown as { __pneumaticConfig?: IPneumaticConfig }).__pneumaticConfig;
    if (pneumaticConfig?.config?.featureFlags && pneumaticConfig.config.featureFlags[key] !== undefined) {
      return pneumaticConfig.config.featureFlags[key];
    }
  }

  return typeof process !== 'undefined' && process.env
    ? process.env[key]
    : undefined;
};

export const envLanguageCode: string | undefined  =     getEnv('LANGUAGE_CODE');
export const envBackendURL: string | undefined =        getEnv('BACKEND_URL');
export const envSentry: string | undefined =            getEnv('SENTRY_DSN');
export const envWssURL: string | undefined =            getEnv('WSS_URL');
export const envDevMode: boolean =  process.env.NODE_ENV === 'development';

export const isEnvCaptcha: boolean =    getEnv('CAPTCHA') !== 'no';
export const isEnvGoogleAuth: boolean = getEnv('GOOGLE_AUTH') !== 'no';
export const isEnvMsAuth: boolean =     getEnv('MS_AUTH') !== 'no';
export const isEnvSSOAuth: boolean =    getEnv('SSO_AUTH') !== 'no';
export const isEnvSignup: boolean =     getEnv('SIGNUP') !== 'no';
export const isEnvBilling: boolean =    getEnv('BILLING') !== 'no';
export const isEnvAi: boolean =         getEnv('AI') !== 'no';
export const isEnvPush: boolean =       getEnv('PUSH') !== 'no';
export const isEnvStorage: boolean =    getEnv('STORAGE') !== 'no';
export const isEnvAnalytics: boolean =  getEnv('ANALYTICS') !== 'no';
export const envSSOProvider: string | undefined = getEnv('SSO_PROVIDER');


// New ENV


export const envHost: string | undefined = getEnv('HOST');
export const envAnalyticsId: string | undefined = getEnv('ANALYTICS_ID');
export const envRecaptchaSiteKey: string | undefined = getEnv('RECAPTCHA_SITE_KEY');

export const envGoogleClientId: string | undefined = getEnv('GOOGLE_CLIENT_ID');
export const envSentryRelease: string | undefined = getEnv('SENTRY_RELEASE');

interface IFirebaseConfig {
  vapidKey: string | undefined;
  config: {
    apiKey: string | undefined;
    authDomain: string | undefined;
    projectId: string | undefined;
    storageBucket: string | undefined;
    messagingSenderId: string | undefined;
    appId: string | undefined;
    measurementId: string | undefined;
  };
}

export const envFirebase: IFirebaseConfig = {
  vapidKey: getEnv('FIREBASE_VAPID_KEY'),
  config: {
    apiKey: getEnv('FIREBASE_API_KEY'),
    authDomain: getEnv('FIREBASE_AUTH_DOMAIN'),
    projectId: getEnv('FIREBASE_PROJECT_ID'),
    storageBucket: getEnv('FIREBASE_STORAGE_BUCKET'),
    messagingSenderId: getEnv('FIREBASE_SENDER_ID'),
    appId: getEnv('FIREBASE_APP_ID'),
    measurementId: getEnv('FIREBASE_MEASUREMENT_ID')
  }
};
