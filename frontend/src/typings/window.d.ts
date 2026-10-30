import { StoreEnhancer, compose } from 'redux';

import { TAnalyticsMethods } from '../public/utils/analytics';
import { IReduxDevToolsOptions } from '../public/types/redux';

declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION_COMPOSE__?: {
      (options: IReduxDevToolsOptions): typeof compose;
      (...funcs: Array<StoreEnhancer>): StoreEnhancer;
    };
    __REDUX_DEVTOOLS_EXTENSION__?: (options?: IReduxDevToolsOptions) => StoreEnhancer;
    Intercom?(...args: any[]): void;
    intercomSettings: object;
    analytics?: TAnalyticsMethods;
  }
}
