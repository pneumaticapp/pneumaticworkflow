import React from 'react';
import { useIntl } from 'react-intl';

import { ERoutes } from '../../constants/routes';
import { isEnvBilling } from '../../constants/enviroment';
import { ESubscriptionPlan } from '../../types/account';
import { history } from '../../utils/history';
import {
  CreditCardIcon,
  IntegrationSmIcon,
  PersonIcon,
  SuitcaseIcon,
  TuneViewIcon,
  TurnOffIcon,
  UsersIcon,
} from '../icons';
import { CurrentUserAvatar, Dropdown, TDropdownOption } from '../UI';
import { TProfileDropdownProps } from './types';

import styles from './TopNav.css';

export function ProfileDropdown({
  firstName,
  lastName,
  leaseLevel,
  plan,
  isAccountOwner,
  isAdmin,
  logoutUser,
  redirectToCustomerPortal,
}: TProfileDropdownProps) {
  const { formatMessage } = useIntl();
  const userFullName = `${firstName} ${lastName}`.trim();
  const showCustomerPortalLink =
    plan !== ESubscriptionPlan.Free &&
    plan !== ESubscriptionPlan.Unknown &&
    isAccountOwner &&
    leaseLevel !== 'tenant';

  const handleOptionClick = (handler: () => void) => (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const profileDropdownOptions = [
    userFullName && {
      label: userFullName,
      className: styles['user-name-item'],
    },
    {
      label: formatMessage({ id: 'nav.profile' }),
      onClick: handleOptionClick(() => history.push(ERoutes.Profile)),
      withUpperline: Boolean(userFullName),
      Icon: PersonIcon,
    },
    {
      label: formatMessage({ id: 'nav.settings' }),
      onClick: handleOptionClick(() => history.push(ERoutes.AccountSettings)),
      Icon: TuneViewIcon,
    },
    isEnvBilling && {
      label: formatMessage({ id: 'nav.pricing' }),
      onClick: handleOptionClick(() => window.open('https://www.pneumatic.app/pricing/')),
      color: 'orange',
      isHidden: leaseLevel === 'tenant',
      Icon: SuitcaseIcon,
    },
    {
      label: formatMessage({ id: 'nav.customer-portal' }),
      onClick: redirectToCustomerPortal,
      isHidden: !showCustomerPortalLink,
      Icon: CreditCardIcon,
    },
    {
      label: formatMessage({ id: 'nav.team' }),
      onClick: handleOptionClick(() => history.push(ERoutes.Team)),
      isHidden: !isAdmin,
      Icon: UsersIcon,
      withUpperline: true,
    },
    {
      label: formatMessage({ id: 'nav.integration' }),
      onClick: handleOptionClick(() => history.push(ERoutes.Integrations)),
      isHidden: !isAdmin,
      Icon: IntegrationSmIcon,
    },
    {
      label: formatMessage({ id: 'user.sign-out' }),
      onClick: handleOptionClick(logoutUser),
      color: 'red',
      withUpperline: true,
      Icon: TurnOffIcon,
    },
  ].filter((item) => typeof item === 'object') as TDropdownOption[];

  return (
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
  );
}
