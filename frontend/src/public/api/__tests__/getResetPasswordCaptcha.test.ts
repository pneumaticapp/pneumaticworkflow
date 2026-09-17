import { configMock } from '../../__stubs__/configMock';
jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue(configMock),
}));
import { commonRequest } from '../commonRequest';
import { getResetPasswordCaptcha } from '../getResetPasswordCaptcha';

jest.mock('../commonRequest');

describe('getResetPasswordCaptcha', () => {
  it('calls commonRequest with the needed parameters', async () => {
    (commonRequest as jest.Mock).mockResolvedValueOnce({ showCaptcha: true });

    const result = await getResetPasswordCaptcha();

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
