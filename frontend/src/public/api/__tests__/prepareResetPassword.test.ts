import { configMock } from '../../__stubs__/configMock';
jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue(configMock),
}));
import { commonRequest } from '../commonRequest';
import { prepareResetPassword } from '../prepareResetPassword';

jest.mock('../commonRequest');

describe('prepareResetPassword', () => {
  it('calls commonRequest with the needed parameters', async () => {
    (commonRequest as jest.Mock).mockResolvedValueOnce({ showCaptcha: true });

    const result = await prepareResetPassword();

    expect(result).toEqual({ showCaptcha: true });
    expect(commonRequest).toHaveBeenCalledWith(
      '/path/to/reset-password/captcha',
      {},
      {
        type: 'local',
        shouldThrow: true,
      },
    );
  });
});
