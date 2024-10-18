import * as React from 'react';
import { IntlProvider } from 'react-intl';
import classnames from 'classnames';
import { RouteComponentProps } from 'react-router-dom';

import { useShouldHideIntercom } from '../../hooks/useShouldHideIntercom';
import { AppLocale } from '../../lang';
import { ELocale, IAuthUser } from '../../types/redux';
import { NotificationContainer } from '../UI/Notifications';
import { FullscreenImageContainer } from '../FullscreenImage';
import { initiatePagesTracking } from '../../utils/analytics/trackPages';
import { useSyncLoggedTabsState } from './syncLoggedTabsState';

import { AppRoutes } from './AppRoutes';
import { useFaviconUpdater } from './useFaviconUpdater';

import styles from './App.css';


import '../../assets/css/vendor/bootstrap.min.css';
import 'react-perfect-scrollbar/dist/css/styles.css';
import 'react-phone-number-input/style.css';
import 'rc-switch/assets/index.css';
import '../../assets/fonts/iconsmind-s/css/iconsminds.css';
import '../../assets/fonts/simple-line-icons/css/simple-line-icons.css';
import '../../assets/css/sass/themes/gogo.light.yellow.scss';
import '../../assets/css/style.css';



export interface IAppProps {
  user: IAuthUser;
  locale: ELocale;
  hasNewNotifications: boolean;
  hasNewTasks: boolean;
  containerClassnames: string;
  isFullscreenImageOpen: boolean;
  showPlanExpiredMessage(): void;
  logoutUser(): void;
}

export type TAppProps = IAppProps & RouteComponentProps;

export function App({
  user,
  locale,
  hasNewNotifications,
  hasNewTasks,
  containerClassnames,
  isFullscreenImageOpen,
  logoutUser,
}: TAppProps) {
  useFaviconUpdater(hasNewNotifications, hasNewTasks);
  useShouldHideIntercom(user.isSupermode);
  useSyncLoggedTabsState(user.loggedState, logoutUser);

  React.useEffect(() => {
    initiatePagesTracking();
  }, []);

  const currentAppLocale = AppLocale[locale];

  return (
    <div className={classnames(styles['pneumatic-frontend-main-wrapper'], 'rounded')}>
      <IntlProvider locale={currentAppLocale.locale} messages={currentAppLocale.messages}>
        <NotificationContainer />
        <AppRoutes
          user={user}
          containerClassnames={containerClassnames}
        />
      </IntlProvider>

      {isFullscreenImageOpen && <FullscreenImageContainer />}
    </div>
  );
}
