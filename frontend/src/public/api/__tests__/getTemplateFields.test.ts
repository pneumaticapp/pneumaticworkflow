// <reference types="jest" />

const MOCK_URLS = {
  templateFields: '/templates/:id/fields',
};

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: { urls: MOCK_URLS },
  }),
}));

jest.mock('../commonRequest');

import { commonRequest } from '../commonRequest';
import { getTemplateFields } from '../getTemplateFields';

describe('getTemplateFields', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls commonRequest with GET, correct URL and signal', async () => {
    const mockResponse = { tasks: [], kickoff: { fields: [], fieldsets: [] } };
    (commonRequest as jest.Mock).mockResolvedValue(mockResponse);

    const abortController = new AbortController();
    const result = await getTemplateFields('42', abortController.signal);

    expect(commonRequest).toHaveBeenCalledTimes(1);
    expect(commonRequest).toHaveBeenCalledWith(
      '/templates/42/fields',
      { signal: abortController.signal },
      { shouldThrow: true },
    );
    expect(result).toBe(mockResponse);
  });
});
