import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { ERoutes } from '../../constants/routes';
import { PaywallReminder } from './PaywallReminder';
import { BellIcon } from '../icons';
import { EPlanActions } from '../../utils/getPlanPendingActions';
import { CurrentUserAvatar, Dropdown, TDropdownOption } from '../UI';
import { history } from '../../utils/history';
import { IAccount, TAccountLeaseLevel } from '../../types/user';
import { truncateString } from '../../utils/truncateString';
import { ESubscriptionPlan } from '../../types/account';

import { EPaywallReminderType } from './utils/getPaywallType';

import styles from './TopNav.css';
import { isEnvBilling } from '../../constants/enviroment';

export interface ITopNavProps {
  pendingActions: EPlanActions[];
  paywallType: EPaywallReminderType | null;
  isSubscribed: boolean;
  unreadNotificationsCount: number;
  isSupermode: boolean;
  tenantName: string;
  leaseLevel: TAccountLeaseLevel;
  isAccountOwner: boolean;
  accountOwnerPlan: IAccount;
}

export interface ITopNavDispatchProps {
  logoutUser(): void;
  setNotificationsListIsOpen(isOpen: boolean): void;
  showPlanExpiredMessage(): void;
  returnFromSupermode(): void;
  redirectToCustomerPortal(): void;
}

export interface ITopNavOwnProps {
  leftContent?: React.ReactNode;
  centerContent?: React.ReactNode;
}

export type TTopNavProps = ITopNavProps & ITopNavDispatchProps & ITopNavOwnProps;

export function TopNav({
  pendingActions,
  paywallType,
  isSubscribed,
  unreadNotificationsCount,
  isSupermode,
  tenantName,
  leaseLevel,
  isAccountOwner,
  leftContent,
  accountOwnerPlan,
  centerContent,
  logoutUser,
  setNotificationsListIsOpen,
  showPlanExpiredMessage,
  returnFromSupermode,
  redirectToCustomerPortal,
}: TTopNavProps) {
  const { formatMessage } = useIntl();

  const isPaywallVisible = Boolean(paywallType);
  const rightNavbarClassname = classnames('navbar-right', styles['navbar-right']);

  const showCustomerPortalLink = isSubscribed && isAccountOwner && leaseLevel !== 'tenant';

  const getColorSuperMode = (billingPlan: ESubscriptionPlan, isTrial: boolean, status: TAccountLeaseLevel) => {
    const statusClassesMap = {
      [ESubscriptionPlan.Unknown]: styles['top-bar__supermode__free'],
      [ESubscriptionPlan.Free]: styles['top-bar__supermode__free'],
      [ESubscriptionPlan.Trial]: styles['top-bar__supermode__trial'],
      [ESubscriptionPlan.Premium]: styles['top-bar__supermode__premium'],
      [ESubscriptionPlan.Unlimited]: styles['top-bar__supermode__premium'],
      [ESubscriptionPlan.FractionalCOO]: styles['top-bar__supermode__premium'],
    };

    if (status === 'partner') {
      return null;
    }

    return isTrial ? styles['top-bar__supermode__trial'] : statusClassesMap[billingPlan];
  };

  const renderPaywallContent = () => {
    if (isSupermode) {
      return (
        <div
          className={classnames(
            styles['top-bar'],
            styles['top-bar__supermode'],
            getColorSuperMode(
              accountOwnerPlan.billingPlan,
              accountOwnerPlan.trialIsActive,
              accountOwnerPlan.leaseLevel,
            ),
          )}
        >
          {formatMessage(
            { id: 'superuser.edit-notification' },
            {
              companyName: truncateString(tenantName, 20),
            },
          )}
          <span></span>
          <button type="button" onClick={returnFromSupermode} className={styles['top-bar__exit-button']}>
            {formatMessage({ id: 'superuser.edit-notification-exit' })}
          </button>
        </div>
      );
    }

    if (!paywallType) {
      return null;
    }

    return <PaywallReminder type={paywallType} pendingActions={pendingActions} />;
  };

  const handleOpenNotifications = () => {
    if (pendingActions.includes(EPlanActions.ChoosePlan)) {
      showPlanExpiredMessage();

      return;
    }

    setNotificationsListIsOpen(true);
  };

  const handleOptionClick = (handler: () => void) => (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const profileDropdownOptions = [
    {
      label: formatMessage({ id: 'nav.profile' }),
      onClick: handleOptionClick(() => history.push(ERoutes.Profile)),
    },
    {
      label: formatMessage({ id: 'nav.settings' }),
      onClick: handleOptionClick(() => history.push(ERoutes.AccountSettings)),
    },
    isEnvBilling && {
      label: formatMessage({ id: 'nav.pricing' }),
      onClick: handleOptionClick(() => window.open('https://www.pneumatic.app/pricing/')),
      color: 'orange',
      isHidden: leaseLevel === 'tenant',
    },
    isEnvBilling && {
      label: formatMessage({ id: 'nav.customer-portal' }),
      onClick: redirectToCustomerPortal,
      isHidden: !showCustomerPortalLink,
    },
    {
      label: formatMessage({ id: 'user.sign-out' }),
      onClick: handleOptionClick(logoutUser),
      color: 'red',
      withUpperline: true,
    },
  ].filter((item) => typeof item === 'object') as TDropdownOption[];

  return (
    <div className={classnames(styles['top-wrapper'], isPaywallVisible && styles['top-wrapper_with-paywall'])}>
      {renderPaywallContent()}
      <nav className={classnames('navbar', styles['navbar'])}>
        {leftContent && <div className={styles['navbar-left']}>{leftContent}</div>}
        {centerContent && <div className={styles['navbar-center']}>{centerContent}</div>}
        <div className={rightNavbarClassname}>
          <div className={styles['notifications']}>
            <button
              type="button"
              onClick={handleOpenNotifications}
              className={styles['notifications-button']}
              aria-label="Notifications"
            >
              {unreadNotificationsCount > 0 && (
                <div className={styles['notification_counter_container']}>
                  <div className={styles['notification_counter_container__counter']}>
                    {unreadNotificationsCount > 99 ? '99+' : unreadNotificationsCount}
                  </div>
                </div>
              )}
              <BellIcon />
            </button>
          </div>
          <div className={styles['user-avatar']}>
            <Dropdown
              renderToggle={() => <CurrentUserAvatar size="md" />}
              toggleProps={{
                'data-test-id': 'open-user-menu-button',
                'aria-label': 'Profile',
                className: styles['profile-button'],
              }}
              className={styles['profile-dropdown']}
              options={profileDropdownOptions}
            />
          </div>
        </div>
      </nav>
    </div>
  );
}
