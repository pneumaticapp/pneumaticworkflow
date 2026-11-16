import { commonRequest } from '../../commonRequest';
import { getInvites } from '../getInvites';
import { makeUserInvite } from '../../../__stubs__/team.factory';
import type { UserInvite } from '../../../redux/team/types';

jest.mock('../../../utils/getConfig', () => {
  const commonConfig = require('../../../../../config/common.json');

  return {
    getBrowserConfigEnv: jest.fn().mockReturnValue({
      api: {
        urls: {
          getInvites: commonConfig.api.urls.getInvites,
        },
      },
    }),
  };
});

jest.mock('../../commonRequest', () => ({
  commonRequest: jest.fn(),
}));

const mockCommonRequest = commonRequest as jest.MockedFunction<typeof commonRequest>;

describe('getInvites API client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls commonRequest with getInvites URL, shouldThrow: true, and returns the invites list', async () => {
    const mockResponse: UserInvite[] = [makeUserInvite()];
    mockCommonRequest.mockResolvedValueOnce(mockResponse);

    const result = await getInvites();

    expect(mockCommonRequest).toHaveBeenCalledTimes(1);
    expect(mockCommonRequest).toHaveBeenCalledWith('/accounts/user/contacts', {}, { shouldThrow: true });
    expect(result).toBe(mockResponse);
  });
});
