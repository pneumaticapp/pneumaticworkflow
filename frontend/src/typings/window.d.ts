import { TAnalyticsMethods } from '../public/utils/analytics';

declare global {
  interface Window {
    Intercom?(...args: any[]): void;
    intercomSettings: object;
    analytics?: TAnalyticsMethods;
  }
}
