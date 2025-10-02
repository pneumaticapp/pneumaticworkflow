import { StoreEnhancer, compose } from 'redux';

import { TAnalyticsMethods } from '../public/utils/analytics';

declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION_COMPOSE__?: typeof compose;
    __REDUX_DEVTOOLS_EXTENSION__?: () => StoreEnhancer<any>;
    Intercom?(...args: any[]): void;
    intercomSettings: object;
    analytics?: TAnalyticsMethods;
  }
}
