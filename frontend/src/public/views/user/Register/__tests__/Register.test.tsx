import * as React from 'react';
import { render, waitFor } from '@testing-library/react';

import { Register } from '../Register';
import { prepareRegisterUser } from '../../../../api/prepareRegisterUser';
import { InterceptorError } from '../../../../api/InterceptorError';
import { logger } from '../../../../utils/logger';

jest.mock('../../../../api/prepareRegisterUser', () => ({
  prepareRegisterUser: jest.fn(),
}));

jest.mock('../../../../api/getGoogleAuthUrl', () => ({
  getOAuthUrl: jest.fn(),
}));

jest.mock('../../../../utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn() },
}));

jest.mock('../../../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({ recaptchaSecret: 'test-secret' }),
}));

jest.mock('../../../../utils/history', () => ({
  history: { location: { search: '' } },
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
  isEnvGoogleAuth: false,
  isEnvMsAuth: false,
  isEnvSSOAuth: false,
  envSSOProvider: undefined,
}));

jest.mock('react-google-recaptcha', () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock('../../../../components/IntlMessages', () => ({
  IntlMessages: () => null,
}));

jest.mock('../../../../components/NavLink', () => ({
  NavLink: ({ children }: { children: React.ReactNode }) => React.createElement('a', null, children),
}));

jest.mock('../../../../components/OAuthButtons', () => ({
  GoogleButton: () => null,
  MicrosoftButton: () => null,
  SSOButton: () => null,
}));

jest.mock('../../../../components/UI/FormikFields', () => ({
  Phone: () => null,
}));

jest.mock('../../../../components/UI', () => ({
  Button: (properties: { label: string }) => React.createElement('button', { type: 'submit' }, properties.label),
  Header: ({ children }: { children: React.ReactNode }) => React.createElement('h2', null, children),
  InputField: (properties: { name: string }) => React.createElement('input', { name: properties.name }),
}));

describe('Register', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('captcha check request failure', () => {
    it('passes the caught error to logger.error', async () => {
      const error = new InterceptorError('Request timeout');
      (prepareRegisterUser as jest.Mock).mockRejectedValue(error);

      render(React.createElement(Register, { registerUser: jest.fn() }));

      await waitFor(() => {
        expect(logger.error).toHaveBeenCalledWith(error);
      });
      expect(logger.error).toHaveBeenCalledTimes(1);
    });
  });
});
