import * as sentry from '@sentry/react';
import { diff } from 'deep-object-diff';

import { IAccount } from '../../types/user';
import { parseCookies } from '../cookie';
import { TAuthUserResult } from '../../redux/auth/actions';
import { TITLES } from '../../constants/titles';
import { store } from '../../redux/store';
import { loadAnalytics } from './segmentSnippet';
import { isObjectEmpty } from '../helpers';
import { isEnvAnalytics } from '../../constants/enviroment';

export interface IAnalyticsParams {
  category: EAnalyticsCategory;
  label: string;
  action: EAnalyticsAction;
}

export enum EAnalyticsCategory {
  Accounts = 'Accounts',
  Invite = 'Invite',
  Video = 'Video',
  Dashboard = 'Dashboard',
  Templates = 'Templates',
  Workflow = 'Workflow',
}

export enum EAnalyticsAction {
  Initiated = 'Initiated',
  Embedded = 'Embedded',
}

const MAX_EVENTS_PER_PERIOD = 100;
const PERIOD = 60 * 1000;
const THROTTLE_GAP = 3 * 1000;

export type TAnalyticsMethods = {
  track(...args: any[]): void;
  page(...args: any[]): void;
  identify(...args: any[]): void;
  group(...args: any[]): void;
  reset(...args: any[]): void;
};

export class Analytics {
  private isThrottleMode = false;

  private eventsCounter = 0;

  private periodStarted = 0;

  public constructor(isSupermode: boolean) {
    if (!isEnvAnalytics || isSupermode) {
      return;
    }

    loadAnalytics();
  }

  private increaseEventsCounter = () => {
    const now = Date.now();
    if (now - this.periodStarted > PERIOD) {
      this.periodStarted = now;
      this.eventsCounter = 1;

      return;
    }

    // eslint-disable-next-line no-plusplus
    this.eventsCounter++;
    if (this.eventsCounter > MAX_EVENTS_PER_PERIOD) {
      sentry.captureException('WARNING! Suspicious user activity.');
      this.isThrottleMode = true;
    }
  };

  private throttle = (methodName: keyof TAnalyticsMethods) => {
    let prevArgs: any[] = [];
    let lastTimeWithThrottle = 0;
    let argumentsChanged = true;

    return (...args: any[]) => {
      this.increaseEventsCounter();
      argumentsChanged = !isObjectEmpty(diff(prevArgs, args));
      prevArgs = args;

      if (!this.isThrottleMode) {
        window.analytics?.[methodName](...args);

        return;
      }

      if (argumentsChanged) {
        window.analytics?.[methodName](...args);

        return;
      }

      const now = Date.now();
      if (now - lastTimeWithThrottle >= THROTTLE_GAP) {
        window.analytics?.[methodName](...args);
        lastTimeWithThrottle = now;
      }
    };
  };

  public send = this.throttle('track') as (eventName: string, params?: Partial<IAnalyticsParams>) => void;

  public page = this.throttle('page');

  public identify = this.throttle('identify');

  public group = this.throttle('group');

  public reset = this.throttle('reset');
}

const isSupermode = store?.getState?.().authUser.isSupermode || false;
export const analytics = new Analytics(isSupermode);

export const trackPage = (...args: any[]) => {
  analytics.page(...args);
};

export const trackGoogleRegistration = () => {
  analytics.page('Google sign up', { title: TITLES.Register });
};

export const identifyUser = (user: TAuthUserResult) => {
  const { id, email, firstName, lastName, photo: avatar, account } = user;
  const { ajs_user_id: analyticsId } = parseCookies(document.cookie);
  if (id && Number(analyticsId) !== id) {
    const name = [firstName, lastName].filter(Boolean).join(' ');
    analytics.identify(id, { avatar, email, name });
    identifyCompany(account);
  }
};

export const identifyCompany = (account: IAccount) => {
  const { id, name } = account;
  const { ajs_group_id: accountId } = parseCookies(document.cookie);
  if (accountId && accountId !== String(id)) {
    analytics.group(id, { name });
  }
};

export const trackShareKickoffForm = () => {
  analytics.send('Click on share kickoff');
};

export const trackInviteTeamInPage = (label: string) => {
  const properties = {
    category: EAnalyticsCategory.Invite,
    label,
    action: EAnalyticsAction.Initiated,
  };

  analytics.send('Invite team', properties);
};

export const trackVideoEmbedding = (videoHostName: string) => {
  analytics.send('Embedding video', {
    category: EAnalyticsCategory.Video,
    label: videoHostName,
    action: EAnalyticsAction.Embedded,
  });
};
