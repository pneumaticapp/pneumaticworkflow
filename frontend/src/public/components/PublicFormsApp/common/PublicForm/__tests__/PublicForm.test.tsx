import * as React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { useDispatch } from 'react-redux';

import { PublicForm } from '../PublicForm';
import { getPublicForm } from '../../../../../api/getPublicForm';
import { EExtraFieldType } from '../../../../../types/template';

jest.mock('../../../../../api/getPublicForm', () => ({
  getPublicForm: jest.fn(),
}));

jest.mock('../../../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn(() => <div data-testid="extra-field" />),
}));

jest.mock('../../../../../utils/getConfig', () => ({
  getPublicFormConfig: () => ({
    config: { recaptchaSecret: 'test-secret' },
  }),
  getBrowserConfigEnv: () => ({
    api: { urls: {} },
  }),
}));

jest.mock('react-google-recaptcha', () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock('../../../../../constants/enviroment', () => ({
  isEnvCaptcha: false,
}));

const makeField = (overrides = {}) => ({
  apiName: `f-${Math.random()}`,
  name: 'Field',
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
  ...overrides,
});

describe('PublicForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(jest.fn());
  });

  describe('Filtering fields by isHidden', () => {
    it('renders only visible fields from a mixed list', async () => {
      (getPublicForm as jest.Mock).mockResolvedValue({
        accountId: 1,
        name: 'Test Form',
        description: '',
        showCaptcha: false,
        kickoff: {
          description: '',
          fields: [
            makeField({ apiName: 'f1', isHidden: true }),
            makeField({ apiName: 'f2', isHidden: false }),
            makeField({ apiName: 'f3' }),
          ],
        },
      });

      render(<PublicForm type="shared" />);

      await waitFor(() => {
        expect(screen.getAllByTestId('extra-field')).toHaveLength(2);
      });
    });
  });
});
