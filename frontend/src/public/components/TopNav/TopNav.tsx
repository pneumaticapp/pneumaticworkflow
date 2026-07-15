import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { PaywallReminder } from './PaywallReminder';
import { BellIcon } from '../icons';
import { EPlanActions } from '../../utils/getPlanPendingActions';
import { TAccountLeaseLevel } from '../../types/user';
import { truncateString } from '../../utils/truncateString';
import { ESubscriptionPlan } from '../../types/account';
import { EWorkflowsView } from '../../types/workflow';
import {
  logoutUser as logoutUserAction,
  redirectToCustomerPortal as redirectToCustomerPortalAction,
  returnFromSupermode as returnFromSupermodeAction,
  setNotificationsListIsOpen as setNotificationsListIsOpenAction,
} from '../../redux/actions';
import { getTopNavState } from '../../redux/selectors/topNav';
import { ProfileDropdown } from './ProfileDropdown';
import { ITopNavProps, TTopNavContentProps } from './types';

import styles from './TopNav.css';

export type { ITopNavProps as ITopNavOwnProps } from './types';

export function TopNav(props: ITopNavProps) {
  const dispatch = useDispatch();
  const stateProps = useSelector(getTopNavState);

  return (
    <TopNavContent
      {...props}
      {...stateProps}
      logoutUser={() => dispatch(logoutUserAction())}
      setNotificationsListIsOpen={(isOpen) => dispatch(setNotificationsListIsOpenAction(isOpen))}
      returnFromSupermode={() => dispatch(returnFromSupermodeAction())}
      redirectToCustomerPortal={() => dispatch(redirectToCustomerPortalAction())}
    />
  );
}

export function TopNavContent({
  pendingActions,
  paywallType,
  plan,
  unreadNotificationsCount,
  isSupermode,
  tenantName,
  leaseLevel,
  isAccountOwner,
  leftContent,
  accountOwnerPlan,
  logoutUser,
  setNotificationsListIsOpen,
  returnFromSupermode,
  redirectToCustomerPortal,
  isFromWorkflowsLayout,
  workflowsView,
  isAdmin,
  firstName,
  lastName,
}: TTopNavContentProps) {
  const { formatMessage } = useIntl();

  const isPaywallVisible = Boolean(paywallType);
  const rightNavbarClassname = classnames('navbar-right', styles['navbar-right']);

  const getColorSuperMode = (billingPlan: ESubscriptionPlan, isTrial: boolean, status: TAccountLeaseLevel) => {
    const statusClassesMap = {
      [ESubscriptionPlan.Unknown]: styles['top-bar__supermode__free'],
      [ESubscriptionPlan.Free]: styles['top-bar__supermode__free'],
      [ESubscriptionPlan.Trial]: styles['top-bar__supermode__trial'],
      [ESubscriptionPlan.Premium]: styles['top-bar__supermode__premium'],
      [ESubscriptionPlan.Unlimited]: styles['top-bar__supermode__premium'],
      [ESubscriptionPlan.FractionalCOO]: styles['top-bar__supermode__premium'],
    };

    if (status === 'partner') return null;

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
    if (pendingActions.includes(EPlanActions.ChoosePlan)) return;

    setNotificationsListIsOpen(true);
  };

  const getWorkflowNavbarClassname = () => {
    if (!isFromWorkflowsLayout) return '';

    return workflowsView === EWorkflowsView.Table
      ? styles['navbar--workflows-table']
      : styles['navbar--workflows-grid'];
  };

  const workflowNavbarClassname = getWorkflowNavbarClassname();

  return (
    <div
      className={classnames(
        'no-print',
        styles['top-wrapper'],
        isFromWorkflowsLayout && styles['top-wrapper--workflows-layout'],
        isPaywallVisible && styles['top-wrapper_with-paywall'],
      )}
    >
      {renderPaywallContent()}
      <nav className={classnames('navbar', styles['navbar'], workflowNavbarClassname)}>
        {leftContent && <div className={styles['navbar-left']}>{leftContent}</div>}
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
            <ProfileDropdown
              firstName={firstName}
              lastName={lastName}
              leaseLevel={leaseLevel}
              plan={plan}
              isAccountOwner={isAccountOwner}
              isAdmin={isAdmin}
              logoutUser={logoutUser}
              redirectToCustomerPortal={redirectToCustomerPortal}
            />
          </div>
        </div>
      </nav>
    </div>
  );
}
