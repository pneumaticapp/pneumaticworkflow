import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { Register } from '../Register';
import { handleOAuthClick } from '../../utils/handleOAuthClick';
import { EOAuthType } from '../../../../types/auth';
import { enMessages } from '../../../../lang/locales/en_US';

const mockOAuthClickHandler = jest.fn();
jest.mock('../../utils/handleOAuthClick', () => ({
  handleOAuthClick: jest.fn(() => mockOAuthClickHandler),
}));

jest.mock('../../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn(() => ({
    recaptchaSecret: 'mock-secret',
  })),
}));

jest.mock('../../../../utils/history', () => ({
  history: {
    location: { search: '' },
  },
  getQueryStringParams: jest.fn(() => ({})),
}));

jest.mock('../../../../components/NavLink', () => ({
  NavLink: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

jest.mock('../../../../constants/enviroment', () => ({
  isEnvGoogleAuth: true,
  isEnvMsAuth: false,
  isEnvSSOAuth: false,
  isEnvCaptcha: false,
  envSSOProvider: 'Auth0',
}));

describe('Register — OAuth button integration', () => {
  const defaultProps = {
    registerUser: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls handleOAuthClick with EOAuthType.Google when Google button is clicked', () => {
    render(
      <IntlProvider locale="en" messages={enMessages}>
        <Register {...defaultProps} />
      </IntlProvider>,
    );

    const googleButton = screen.getByRole('button', { name: /google/i });
    userEvent.click(googleButton);

    expect(handleOAuthClick).toHaveBeenCalledWith(EOAuthType.Google, expect.any(Function));
    expect(mockOAuthClickHandler).toHaveBeenCalledTimes(1);
  });
});
