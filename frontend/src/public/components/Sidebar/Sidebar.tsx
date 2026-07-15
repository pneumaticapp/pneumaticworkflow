import React, { useCallback } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { ERoutes } from '../../constants/routes';
import { openSelectTemplateModal } from '../../redux/actions';
import { getSidebarState } from '../../redux/selectors/sidebar';
import { ESubscriptionPlan } from '../../types/account';
import { EPlanActions } from '../../utils/getPlanPendingActions';
import { NavLink } from '../NavLink';
import { LogoContainer } from '../Logo';
import { RibbonTail } from '../icons';
import { checkHasTopBar } from '../TopNav/utils/checkHasTopBar';

import { SidebarMenu } from './SidebarMenu';
import { SidebarRibbon } from './SidebarRibbon';
import { useSidebarNavigation } from './useSidebarNavigation';
import styles from './Sidebar.css';

const statusClassesMap = {
  [ESubscriptionPlan.Unknown]: styles['sidebar_free'],
  [ESubscriptionPlan.Free]: styles['sidebar_free'],
  [ESubscriptionPlan.Trial]: styles['sidebar_trial'],
  [ESubscriptionPlan.Premium]: styles['sidebar_premium'],
  [ESubscriptionPlan.Unlimited]: styles['sidebar_premium'],
  [ESubscriptionPlan.FractionalCOO]: styles['sidebar_premium'],
};

export function Sidebar() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const {
    authUser: {
      account: { isBlocked, billingPlan: plan, leaseLevel, trialIsActive },
      isSupermode,
    },
    containerClassnames,
    menuHiddenBreakpoint,
    menuItems,
    pendingActions,
  } = useSelector(getSidebarState);
  const {
    activeItemId,
    closeMenu,
    containerRef,
    handleCloseMenu,
    handleMobileMenuToggle,
    handleOpenMenu,
    isMobile,
  } = useSidebarNavigation({
    containerClassnames,
    menuHiddenBreakpoint,
    menuItems,
  });
  const extraSpace = checkHasTopBar(Boolean(isBlocked), plan, Boolean(isSupermode));
  const handleRunWorkflow = useCallback(() => {
    if (!pendingActions.includes(EPlanActions.ChoosePlan)) {
      dispatch(openSelectTemplateModal());
    }
  }, [dispatch, pendingActions]);

  return (
    <div
      ref={containerRef}
      className={classnames(
        'no-print',
        'sidebar',
        styles['sidebar'],
        trialIsActive ? styles['sidebar_trial'] : statusClassesMap[plan],
        leaseLevel === 'partner' && styles['sidebar_partner'],
      )}
      onMouseOver={handleOpenMenu}
      onFocus={handleOpenMenu}
      onMouseLeave={handleCloseMenu}
    >
      <NavLink
        aria-label="Go to Dashboard"
        to={ERoutes.Main}
        onClick={handleMobileMenuToggle}
        className={classnames(styles['logo-mobile'], extraSpace && styles['logo__extra-space'])}
      >
        <LogoContainer className={classnames('active', styles['logo'])} size="sm" theme="light" />
        <RibbonTail className={styles['sidebar-ribbon-tail']} />
      </NavLink>
      <div className={classnames('main-menu', styles['sidebar_menu'], extraSpace && styles['menu__extra-space'])}>
        <NavLink to={ERoutes.Main} className={styles['logo-desktop']}>
          <LogoContainer size="md" className={classnames('active', styles['logo'])} theme="light" />
        </NavLink>
        <div className={styles['sidebar-ribbon']}>
          <SidebarRibbon
            formatMessage={formatMessage}
            leaseLevel={leaseLevel}
            plan={plan}
            trialIsActive={trialIsActive}
          />
          <RibbonTail className={styles['sidebar-ribbon-tail']} />
        </div>
        <SidebarMenu
          activeItemId={activeItemId}
          containerClassnames={containerClassnames}
          isMobile={isMobile}
          menuItems={menuItems}
          onCloseMenu={closeMenu}
          onRunWorkflow={handleRunWorkflow}
          plan={plan}
        />
      </div>
    </div>
  );
}
