export const envLanguageCode: string | undefined  =     process.env.LANGUAGE_CODE;
export const envBackendURL: string | undefined =        process.env.BACKEND_URL;
export const envSentry: string | undefined =            process.env.SENTRY_DSN;
export const envWssURL: string | undefined =            process.env.WSS_URL;
export const envBackendPrivateIP: string | undefined =  process.env.BACKEND_PRIVATE_IP;

export const isEnvCaptcha: boolean =    process.env.CAPTCHA !== 'no';
export const isEnvGoogleAuth: boolean = process.env.GOOGLE_AUTH !== 'no';
export const isEnvMsAuth: boolean =     process.env.MS_AUTH !== 'no';
export const isEnvSSOAuth: boolean =    process.env.SSO_AUTH !== 'no';
export const isEnvSignup: boolean =     process.env.SIGNUP !== 'no';
export const isEnvBilling: boolean =    process.env.BILLING !== 'no';
export const isEnvAi: boolean =         process.env.AI !== 'no';
export const isEnvPush: boolean =       process.env.PUSH !== 'no';
export const isEnvStorage: boolean =    process.env.STORAGE !== 'no';
export const isEnvAnalytics: boolean =  process.env.ANALYTICS !== 'no';


// New ENV


export const envHost: string | undefined = process.env.HOST;
export const envAnalyticsId: string | undefined = process.env.ANALYTICS_ID;
export const envRecaptchaSecret: string | undefined = process.env.RECAPTCHA_SECRET;

export const envGoogleClientId: string | undefined = process.env.GOOGLE_CLIENT_ID;
export const envGoogleClientSecret: string | undefined = process.env.GOOGLE_CLIENT_SECRET;

export const envFirebase: any = {
  vapidKey: process.env.FIREBASE_VAPID_KEY,
  config: {
    apiKey: process.env.FIREBASE_API_KEY,
    authDomain: process.env.FIREBASE_AUTH_DOMAIN,
    projectId: process.env.FIREBASE_PROJECT_ID,
    storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.FIREBASE_APP_ID,
    measurementId: process.env.FIREBASE_MEASUREMENT_ID
  }
};
