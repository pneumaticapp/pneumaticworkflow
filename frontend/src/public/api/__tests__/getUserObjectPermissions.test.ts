const MOCK_URLS = {
  userObjectPermissions: '/accounts/user/permission',
};

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: { urls: MOCK_URLS },
  }),
}));

jest.mock('../commonRequest');

import { commonRequest } from '../commonRequest';
import { getUserObjectPermissions } from '../getUserObjectPermissions';
import { EPermissionObjectType } from '../../types/permissions';

describe('getUserObjectPermissions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('sends the object type and a comma separated list of ids as query params', async () => {
    const mockResponse = [{ id: 1, hasView: true, hasChange: false }];
    (commonRequest as jest.Mock).mockResolvedValue(mockResponse);

    const result = await getUserObjectPermissions({
      objType: EPermissionObjectType.Workflow,
      objIds: [1, 2, 3],
    });

    expect(commonRequest).toHaveBeenCalledWith(
      '/accounts/user/permission?obj_type=workflow&obj_ids=1,2,3',
      {},
      { shouldThrow: true },
    );
    expect(result).toBe(mockResponse);
  });
});
