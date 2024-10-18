/* eslint-disable */
/* prettier-ignore */
import { history } from '../history';
import { trackPage } from './analytics';
import { getAnalyticsPageParams } from './utils';

export interface IHistoryLog {
  lastLocation: Location | null;
}

const historyLog: IHistoryLog = {
  lastLocation: null,
};

export const initiatePagesTracking = () => {
  history.listen((location, action) => {
    if (action === 'REPLACE') {
      return;
    }

    const isNewLocation = !historyLog.lastLocation || historyLog.lastLocation.pathname !== location.pathname;
    const isSearchChanged = historyLog.lastLocation?.search !== location.search;
    if (!isNewLocation || !isSearchChanged) {
      return;
    }

    const { pathname, search } = location;
    trackPage(...getAnalyticsPageParams(pathname, search));
  });
};
