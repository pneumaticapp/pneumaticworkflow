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
