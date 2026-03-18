import * as Sentry from '@sentry/react';

export interface ISentryUserPayload {
  id?: number;
  email?: string;
}

export const setSentryUser = (user: ISentryUserPayload | null): void => {
  if (user === null) {
    Sentry.setUser(null);
    return;
  }
  Sentry.setUser({
    id: user.id !== undefined ? String(user.id) : undefined,
    email: user.email,
  });
};
