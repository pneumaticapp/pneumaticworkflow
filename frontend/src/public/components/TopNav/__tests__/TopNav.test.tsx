// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';

import { TopNav, TTopNavProps } from '../TopNav';
import { Dropdown } from '../../UI';
import { intlMock } from '../../../__stubs__/intlMock';

jest.mock('../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
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

  const baseProps: TTopNavProps = {
    pendingActions: [],
    paywallType: null,
    isSubscribed: false,
    unreadNotificationsCount: 0,
    isSupermode: false,
    tenantName: '',
    leaseLevel: 'standard',
    isAccountOwner: false,
    accountOwnerPlan: {
      billingPlan: 'free',
      plan: 'free',
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
    } as any,
    isAdmin: false,
    firstName: '',
    lastName: '',
    logoutUser: jest.fn(),
    setNotificationsListIsOpen: jest.fn(),
    returnFromSupermode: jest.fn(),
    redirectToCustomerPortal: jest.fn(),
  };

  const getDropdownOptions = () => {
    const dropdownMock = Dropdown as jest.Mock;
    const lastCall = dropdownMock.mock.calls[dropdownMock.mock.calls.length - 1];
    return lastCall[0].options;
  };

  const findOption = (label: string) => {
    const options = getDropdownOptions();
    return options.find((opt: any) => opt.label === label);
  };

  const renderTopNav = (props: Partial<TTopNavProps> = {}) => {
    return render(React.createElement(TopNav, { ...baseProps, ...props }));
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
      const hasNameOption = options.some(
        (opt: any) => opt.label === '' || opt.label === ' ',
      );
      expect(hasNameOption).toBe(false);

      const profileOption = findOption(PROFILE_LABEL);
      expect(profileOption.withUpperline).toBe(false);
    });
  });
});
