jest.mock('../../utils/getConfig', () => {
  const commonConfig = require('../../../../config/common.json');
  return {
    getBrowserConfigEnv: jest.fn().mockReturnValue({
      api: {
        urls: {
          fcmDeviceToken: commonConfig.api.urls.fcmDeviceToken,
        },
      },
    }),
  };
});

jest.mock('../commonRequest', () => ({
  commonRequest: jest.fn(),
}));

import { commonRequest } from '../commonRequest';
import { resetFirebaseDeviceToken } from '../resetFirebaseDeviceToken';

const mockCommonRequest = commonRequest as jest.MockedFunction<typeof commonRequest>;

describe('resetFirebaseDeviceToken API client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls commonRequest with DELETE method, token in URL, and expectedErrorStatuses: [404]', () => {
    const testToken = 'test-firebase-token-12345';
    resetFirebaseDeviceToken(testToken);

    expect(mockCommonRequest).toHaveBeenCalledTimes(1);
    expect(mockCommonRequest).toHaveBeenCalledWith(
      `/notifications/device/${testToken}`,
      {
        method: 'DELETE',
      },
      {
        shouldThrow: false,
        responseType: 'empty',
        expectedErrorStatuses: [404],
      },
    );
  });
});
