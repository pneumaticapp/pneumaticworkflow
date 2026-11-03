import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';

import { Register, IRegisterProps } from '../Register';
import { prepareRegisterUser } from '../../../../api/prepareRegisterUser';
import { InterceptorError } from '../../../../api/InterceptorError';
import { logger } from '../../../../utils/logger';
import { handleOAuthClick } from '../../utils/handleOAuthClick';
import { EOAuthType } from '../../../../types/auth';
import { enMessages } from '../../../../lang/locales/en_US';

const mockOAuthClickHandler = jest.fn();
jest.mock('../../utils/handleOAuthClick', () => ({
  handleOAuthClick: jest.fn(() => mockOAuthClickHandler),
}));

jest.mock('../../../../api/prepareRegisterUser', () => ({
  prepareRegisterUser: jest.fn(),
}));

jest.mock('../../../../utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn() },
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

jest.mock('../../../../utils/landingTemplate', () => ({
  setLandingTemplate: jest.fn(),
}));

jest.mock('../../utils/utmParams', () => ({
  saveUTMParams: jest.fn(),
}));

jest.mock('../utils/templateName', () => ({
  setTemplateName: jest.fn(),
}));

jest.mock('../../../../constants/enviroment', () => ({
  isEnvCaptcha: true,
  isEnvGoogleAuth: true,
  isEnvMsAuth: false,
  isEnvSSOAuth: false,
  envSSOProvider: 'Auth0',
}));

jest.mock('react-google-recaptcha', () => ({
  __esModule: true,
  default: () => React.createElement('div', { role: 'group', 'aria-label': 'captcha' }),
}));

jest.mock('../../../../components/NavLink', () => ({
  NavLink: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

describe('Register', () => {
  const defaultProps: IRegisterProps = {
    registerUser: jest.fn(),
  };

  const renderComponent = (props: Partial<IRegisterProps> = {}) =>
    render(
      <IntlProvider locale="en" messages={enMessages}>
        <Register {...defaultProps} {...props} />
      </IntlProvider>,
    );

  beforeEach(() => {
    jest.clearAllMocks();
    (prepareRegisterUser as jest.Mock).mockResolvedValue({ showCaptcha: false });
  });

  describe('OAuth button integration', () => {
    it('calls handleOAuthClick with EOAuthType.Google when Google button is clicked', () => {
      renderComponent();

      const googleButton = screen.getByRole('button', { name: /google/i });
      userEvent.click(googleButton);

      expect(handleOAuthClick).toHaveBeenCalledWith(EOAuthType.Google, expect.any(Function));
      expect(mockOAuthClickHandler).toHaveBeenCalledTimes(1);
    });
  });

  describe('captcha visibility by showCaptcha field', () => {
    const CAPTCHA_LABEL = 'captcha';

    it('shows captcha when showCaptcha is true', async () => {
      (prepareRegisterUser as jest.Mock).mockResolvedValue({ showCaptcha: true });

      renderComponent();

      expect(await screen.findByRole('group', { name: CAPTCHA_LABEL })).toBeInTheDocument();
    });

    it('does not show captcha when showCaptcha is false', async () => {
      (prepareRegisterUser as jest.Mock).mockResolvedValue({ showCaptcha: false });

      renderComponent();

      await waitFor(() => {
        expect(prepareRegisterUser).toHaveBeenCalledTimes(1);
      });
      expect(screen.queryByRole('group', { name: CAPTCHA_LABEL })).not.toBeInTheDocument();
    });

    it('does not show captcha when showCaptcha is undefined', async () => {
      (prepareRegisterUser as jest.Mock).mockResolvedValue({ showCaptcha: undefined });

      renderComponent();

      await waitFor(() => {
        expect(prepareRegisterUser).toHaveBeenCalledTimes(1);
      });
      expect(screen.queryByRole('group', { name: CAPTCHA_LABEL })).not.toBeInTheDocument();
    });
  });

  describe('captcha check request failure', () => {
    it('passes the caught error to logger.error', async () => {
      const error = new InterceptorError('Request timeout');
      (prepareRegisterUser as jest.Mock).mockRejectedValue(error);

      renderComponent();

      await waitFor(() => {
        expect(logger.error).toHaveBeenCalledWith(error);
      });
      expect(logger.error).toHaveBeenCalledTimes(1);
    });
  });
});
