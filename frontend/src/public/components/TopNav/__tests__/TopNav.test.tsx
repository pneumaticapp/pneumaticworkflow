import * as React from 'react';
import { render } from '@testing-library/react';

import { TopNavContent } from '../TopNav';
import { TTopNavContentProps } from '../types';
import { Dropdown, TDropdownOption } from '../../UI';
import { intlMock } from '../../../__stubs__/intlMock';
import { ESubscriptionPlan } from '../../../types/account';
import { IAccount } from '../../../types/user';

jest.mock('../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../constants/enviroment', () => ({
  isEnvBilling: false,
}));

jest.mock('../PaywallReminder', () => ({
  PaywallReminder: () => null,
}));

jest.mock('../../UI', () => ({
  Dropdown: jest.fn(() => null),
  CurrentUserAvatar: () => null,
}));

jest.mock('../../icons', () => {
  const stub = () => null;
  return {
    BellIcon: stub,
    PersonIcon: stub,
    TuneViewIcon: stub,
    SuitcaseIcon: stub,
    CreditCardIcon: stub,
    UsersIcon: stub,
    IntegrationSmIcon: stub,
    TurnOffIcon: stub,
  };
});

describe('TopNav', () => {
  const t = (id: string) => intlMock.formatMessage({ id });

  const TEAM_LABEL = t('nav.team');
  const INTEGRATION_LABEL = t('nav.integration');
  const PROFILE_LABEL = t('nav.profile');
  const CUSTOMER_PORTAL_LABEL = t('nav.customer-portal');

  const accountOwnerPlan: IAccount = {
    billingPlan: ESubscriptionPlan.Free,
    plan: ESubscriptionPlan.Free,
    isSubscribed: false,
    billingSync: false,
    name: '',
    tenantName: '',
    planExpiration: null,
    leaseLevel: 'standard',
    logoSm: null,
    logoLg: null,
    trialEnded: false,
    trialIsActive: false,
  };

  const baseProps: TTopNavContentProps = {
    pendingActions: [],
    paywallType: null,
    plan: ESubscriptionPlan.Free,
    unreadNotificationsCount: 0,
    isSupermode: false,
    tenantName: '',
    leaseLevel: 'standard',
    isAccountOwner: false,
    accountOwnerPlan,
    isAdmin: false,
    firstName: '',
    lastName: '',
    logoutUser: jest.fn(),
    setNotificationsListIsOpen: jest.fn(),
    returnFromSupermode: jest.fn(),
    redirectToCustomerPortal: jest.fn(),
  };

  const getDropdownOptions = () => {
    const dropdownMock = Dropdown as jest.MockedFunction<typeof Dropdown>;
    const lastCall = dropdownMock.mock.calls[dropdownMock.mock.calls.length - 1];
    const { options } = lastCall[0];

    return (Array.isArray(options) ? options : [options]) as TDropdownOption[];
  };

  const findOption = (label: string) => {
    const options = getDropdownOptions();
    const option = options.find((dropdownOption) => dropdownOption.label === label);

    if (!option) {
      throw new Error(`Dropdown option not found: ${label}`);
    }

    return option;
  };

  const renderTopNav = (props: Partial<TTopNavContentProps> = {}) => {
    return render(React.createElement(TopNavContent, { ...baseProps, ...props }));
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Team and Integration visibility based on isAdmin', () => {
    it('passes isHidden=false for Team and Integration when isAdmin=true', () => {
      renderTopNav({ isAdmin: true });

      const teamOption = findOption(TEAM_LABEL);
      const integrationOption = findOption(INTEGRATION_LABEL);

      expect(teamOption).toBeDefined();
      expect(teamOption.isHidden).toBe(false);
      expect(integrationOption).toBeDefined();
      expect(integrationOption.isHidden).toBe(false);
    });

    it('passes isHidden=true for Team and Integration when isAdmin=false', () => {
      renderTopNav({ isAdmin: false });

      const teamOption = findOption(TEAM_LABEL);
      const integrationOption = findOption(INTEGRATION_LABEL);

      expect(teamOption).toBeDefined();
      expect(teamOption.isHidden).toBe(true);
      expect(integrationOption).toBeDefined();
      expect(integrationOption.isHidden).toBe(true);
    });
  });

  describe('My subscription visibility', () => {
    it('shows My subscription when billing is disabled and plan is paid', () => {
      renderTopNav({ plan: ESubscriptionPlan.Premium, isAccountOwner: true });

      const option = findOption(CUSTOMER_PORTAL_LABEL);
      expect(option).toBeDefined();
      expect(option.isHidden).toBe(false);
    });

    it('hides My subscription when plan is free', () => {
      renderTopNav({ plan: ESubscriptionPlan.Free, isAccountOwner: true });

      const option = findOption(CUSTOMER_PORTAL_LABEL);
      expect(option).toBeDefined();
      expect(option.isHidden).toBe(true);
    });

    it('shows My subscription for a paid partner account owner', () => {
      renderTopNav({ plan: ESubscriptionPlan.Premium, isAccountOwner: true, leaseLevel: 'partner' });

      const option = findOption(CUSTOMER_PORTAL_LABEL);
      expect(option).toBeDefined();
      expect(option.isHidden).toBe(false);
    });

    it('hides My subscription when plan is unknown', () => {
      renderTopNav({ plan: ESubscriptionPlan.Unknown, isAccountOwner: true });

      const option = findOption(CUSTOMER_PORTAL_LABEL);
      expect(option).toBeDefined();
      expect(option.isHidden).toBe(true);
    });

    it('hides My subscription for tenant lease level', () => {
      renderTopNav({ plan: ESubscriptionPlan.Premium, isAccountOwner: true, leaseLevel: 'tenant' });

      const option = findOption(CUSTOMER_PORTAL_LABEL);
      expect(option).toBeDefined();
      expect(option.isHidden).toBe(true);
    });
  });

  describe('User full name display', () => {
    it('passes full user name as the first option', () => {
      renderTopNav({ firstName: 'John', lastName: 'Doe' });

      const options = getDropdownOptions();
      expect(options[0].label).toBe('John Doe');

      const profileOption = findOption(PROFILE_LABEL);
      expect(profileOption.withUpperline).toBe(true);
    });

    it('does not include a name option when firstName and lastName are empty', () => {
      renderTopNav({ firstName: '', lastName: '' });

      const options = getDropdownOptions();
      const hasNameOption = options.some((option) => option.label === '' || option.label === ' ');
      expect(hasNameOption).toBe(false);

      const profileOption = findOption(PROFILE_LABEL);
      expect(profileOption.withUpperline).toBe(false);
    });
  });
});
